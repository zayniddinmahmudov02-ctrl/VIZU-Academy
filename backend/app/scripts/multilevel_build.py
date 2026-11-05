"""Build the Multilevel Modelltest content files (developer tool, runs locally — never on production).

    python -m app.scripts.multilevel_build --number 1 --lesen <lesen-v1.json> --src <v1-rest.ml> --pdf "Multilevel Mock Variant 1.pdf" --images <dir>
    python -m app.scripts.multilevel_build --number 7 --src <mt07.ml> --origin vizu

Inputs: the Lesen part parsed from a text PDF (JSON) and/or ".ml" source files (a small line format, see parse_ml).
Output: app/data/multilevel/modelltest-NN.json (+ images/mtNN-*.jpg), read by app.scripts.multilevel_import.
Keys: PDF imports never carry keys ("correct": null everywhere); VIZU-authored tests mark the right option with "*".

.ml format (one statement per line):
    === LESEN|HOEREN|SCHREIBEN|SPRECHEN        new Kompetenz
    --- Teil 1 | pages=2,3 | words=150 | images=a.jpg,b.jpg | same_situation
    > instruction line          : text line (": ---" = section break)          ! check-list note
    OPTS a | b | c              shared options for the following Q lines without own options
    Q A6 [TF|MATCHING|ORDERING] | question | option | *correct option | option"""

import argparse
import json
import re
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data" / "multilevel"
TYPES = {"LESEN": "Lesen", "HOEREN": "Hören", "SCHREIBEN": "Schreiben", "SPRECHEN": "Sprechen"}
DURATION = {"LESEN": 60, "HOEREN": 40, "SCHREIBEN": 60, "SPRECHEN": 15}
QTYPE = {"TF": "TRUE_FALSE", "MATCHING": "MATCHING", "ORDERING": "ORDERING", "ABC": "SINGLE_CHOICE"}


def words(text: str) -> int:
    return len(re.findall(r"[0-9A-Za-zÄÖÜäöüß]+(?:[’'\-][0-9A-Za-zÄÖÜäöüß]+)*", text or ""))


def parse_ml(path: Path) -> tuple[list[dict], list[dict]]:
    komps, review, komp, teil, opts = [], [], None, None, None
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.replace("﻿", "").rstrip()
        if not line.strip():
            continue
        if line.startswith("=== "):
            kt = line[4:].strip().upper()
            komp = next((k for k in komps if k["type"] == kt), None)
            if komp is None:
                komp = {"type": kt, "teile": []}
                komps.append(komp)
            teil, opts = None, None
            continue
        if line.startswith("--- "):
            head, *attrs = [p.strip() for p in line[4:].split("|")]
            teil = {"title": head, "instructions": [], "text": [], "questions": [], "pages": [], "words": None, "images": [], "same_situation": False}
            for a in attrs:
                k, _, v = a.partition("=")
                if k == "pages":
                    teil["pages"] = [int(x) for x in v.split(",") if x]
                elif k == "words":
                    teil["words"] = int(v)
                elif k == "images":
                    teil["images"] = [x for x in v.split(",") if x]
                elif k == "same_situation":
                    teil["same_situation"] = True
            komp["teile"].append(teil)
            opts = None
            continue
        if line.startswith("! "):
            where = f"{TYPES.get(komp['type'], '') if komp else ''} {teil['title'] if teil else ''}".strip()
            review.append({"where": where or "allgemein", "note": line[2:].strip()})
            continue
        if teil is None:
            raise ValueError(f"{path.name}: line outside a Teil: {line}")
        if line.startswith("> "):
            teil["instructions"].append(line[2:].strip())
        elif line.startswith(":"):
            t = line[1:].strip()
            teil["text"].append("" if t == "---" else t)
        elif line.startswith("OPTS "):
            opts = [o.strip() for o in line[5:].split("|")]
        elif line.startswith("Q "):
            parts = [p.strip() for p in line[2:].split("|")]
            head = parts[0].split()
            no, qt = head[0], QTYPE.get(head[1] if len(head) > 1 else "ABC", "SINGLE_CHOICE")
            text, own = parts[1], parts[2:]
            options = own or list(opts or [])
            if qt == "SINGLE_CHOICE" and not own and opts:
                qt = "MATCHING"
            if len(options) < 2:
                raise ValueError(f"{path.name}: {no} has no options")
            teil["questions"].append({
                "no": no, "type": qt, "text": text,
                "options": [{"text": o.lstrip("*").strip(), "correct": (True if o.startswith("*") else None)} for o in options],
            })
        else:
            raise ValueError(f"{path.name}: unknown line: {line}")
    for k in komps:
        for t in k["teile"]:
            t["instructions"] = "\n".join(t["instructions"])
            t["text"] = "\n".join(t["text"]).strip()
    return komps, review


def lesen_from_parser(path: Path) -> dict:
    teile = []
    for t in json.loads(path.read_text(encoding="utf-8")):
        intro = t.get("intro") or ""
        teile.append({
            "title": f"Teil {t['teil']}", "pages": t["pages"],
            "instructions": "\n".join(x for x in (t["instructions"], intro) if x).strip(),
            "text": t.get("text", ""), "words": None, "images": [], "same_situation": False,
            "questions": [{"no": q["no"], "type": q["type"], "text": q["text"],
                           "options": [{"text": o["text"], "correct": None} for o in q["options"]]} for q in t["questions"]],
        })
    return {"type": "LESEN", "teile": teile}


def combine_images(number: int, idx: int, names: list[str], src: Path) -> str:
    """One image per Sprechen task: two photos side by side (same height), else the single file."""
    from PIL import Image

    out_dir = DATA / "images"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"mt{number:02d}-{idx}.jpg"
    imgs = [Image.open(src / n).convert("RGB") for n in names]
    h = min(i.height for i in imgs)
    imgs = [i.resize((round(i.width * h / i.height), h)) for i in imgs]
    gap = 16 if len(imgs) > 1 else 0
    canvas = Image.new("RGB", (sum(i.width for i in imgs) + gap * (len(imgs) - 1), h), "white")
    x = 0
    for i in imgs:
        canvas.paste(i, (x, 0))
        x += i.width + gap
    if canvas.width > 1600:
        canvas = canvas.resize((1600, round(canvas.height * 1600 / canvas.width)))
    canvas.save(out, "JPEG", quality=85, optimize=True)
    return out.name


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--number", type=int, required=True)
    ap.add_argument("--lesen")
    ap.add_argument("--src", action="append", default=[])
    ap.add_argument("--pdf")
    ap.add_argument("--images")
    ap.add_argument("--origin", choices=("pdf", "vizu"), default="pdf")
    a = ap.parse_args()

    komps, review = [], []
    if a.lesen:
        komps.append(lesen_from_parser(Path(a.lesen)))
    for s in a.src:
        k, r = parse_ml(Path(s))
        for kk in k:
            existing = next((x for x in komps if x["type"] == kk["type"]), None)
            if existing:
                existing["teile"].extend(kk["teile"])
            else:
                komps.append(kk)
        review.extend(r)
    order = list(TYPES)
    komps.sort(key=lambda k: order.index(k["type"]))
    img_idx = 0
    for k in komps:
        k["title"] = TYPES[k["type"]]
        k["duration_minutes"] = DURATION[k["type"]]
        k["total_points"] = sum(len(t["questions"]) for t in k["teile"]) if k["type"] in ("LESEN", "HOEREN") else 0
        for t in k["teile"]:
            t["text_words"] = words(t["text"])
            if t["images"]:
                img_idx += 1
                t["image"] = combine_images(a.number, img_idx, t["images"], Path(a.images))
            t.pop("images", None)
    if a.origin == "pdf":
        review.insert(0, {"where": "allgemein", "note": "Im PDF gibt es keine Lösungen: alle Antwortschlüssel fehlen und müssen im Admin-Panel eingetragen werden."})
        review.insert(1, {"where": "allgemein", "note": "Zeiten (Lesen 60, Hören 40, Schreiben 60, Sprechen 15 Min.) und Bewertungskriterien stehen nicht im PDF — Standardwerte, bitte prüfen."})
        if not any(k["type"] == "HOEREN" for k in komps):
            review.append({"where": "Hören", "note": "Kein Hören-Teil im PDF."})
    doc = {
        "number": a.number,
        "content_id": f"vizu-multilevel-mt{a.number:02d}",
        "title": f"Modelltest {a.number}",
        "origin": a.origin,
        "source_pdf": a.pdf,
        "description": (f"Multilevel Modelltest {a.number} — aus „{a.pdf}“ (Der Deutschlehrer: Zayniddinkhuja Makhmudov)."
                        if a.origin == "pdf" else
                        f"Multilevel Modelltest {a.number} — von VIZU erstellt (Übungstest, kein offizielles Prüfungsmaterial)."),
        "kompetenzen": komps,
        "review": review,
    }
    DATA.mkdir(parents=True, exist_ok=True)
    out = DATA / f"modelltest-{a.number:02d}.json"
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    summary = ", ".join(f"{k['title']} {len(k['teile'])} Teile/{sum(len(t['questions']) for t in k['teile'])} Fragen" for k in komps)
    print(f"{out.name}: {summary}; review={len(review)}")


if __name__ == "__main__":
    main()
