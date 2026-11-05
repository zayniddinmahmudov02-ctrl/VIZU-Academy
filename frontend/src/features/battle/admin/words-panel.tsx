"use client";

import { useEffect, useState, type FormEvent } from "react";
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ExternalLink, ImagePlus, Search, X } from "lucide-react";

import { AdminButton, AdminCard, AdminInput, AdminSelect } from "@/components/admin/admin-ui";
import {
  addBattleWord, fetchImageBlobUrl, getBattleOverview, getBattleWords, importCommons, patchBattleWord, searchCommons, setImageStatus, uploadBattleImage,
  type AdminWord, type ImageStatus,
} from "@/features/admin/services/battle-admin-service";
import { apiErrorMessage } from "@/features/admin/services/lesson-skills-admin-service";
import { cn } from "@/lib/utils";

const STATUS_STYLE: Record<string, string> = {
  published: "bg-emerald-500/15 text-emerald-300 ring-emerald-500/40",
  verified: "bg-sky-500/15 text-sky-300 ring-sky-500/40",
  draft: "bg-amber-500/15 text-amber-300 ring-amber-500/40",
  rejected: "bg-red-500/15 text-red-300 ring-red-500/40",
  disabled: "bg-zinc-500/15 text-zinc-300 ring-zinc-500/40",
};

function Badge({ s }: { s: string }) {
  return <span className={cn("rounded-full px-2 py-0.5 text-[11px] font-semibold ring-1", STATUS_STYLE[s] ?? STATUS_STYLE.draft)}>{s}</span>;
}

function PrivateImage({ id, className }: { id: string; className?: string }) {
  const { data } = useQuery({ queryKey: ["admin-battle-image", id], queryFn: () => fetchImageBlobUrl(id), staleTime: Infinity, gcTime: 5 * 60_000 });
  useEffect(() => () => { if (data) URL.revokeObjectURL(data); }, [data]);
  // eslint-disable-next-line @next/next/no-img-element -- private blob URL
  return data ? <img src={data} alt="" className={className} /> : <div className={cn("animate-pulse bg-[var(--admin-hover)]", className)} />;
}

export default function WordsPanel() {
  const qc = useQueryClient();
  const [filters, setFilters] = useState({ level: "", status: "", category: "", q: "", page: 1 });
  const [selected, setSelected] = useState<AdminWord | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const overview = useQuery({ queryKey: ["admin-battle-overview"], queryFn: getBattleOverview });
  const words = useQuery({ queryKey: ["admin-battle-words", filters], queryFn: () => getBattleWords(filters), placeholderData: keepPreviousData });
  const categories = overview.data?.categories ?? {};
  const refresh = (w?: AdminWord) => {
    qc.invalidateQueries({ queryKey: ["admin-battle-words"] });
    qc.invalidateQueries({ queryKey: ["admin-battle-overview"] });
    if (w) setSelected(w);
  };
  const onError = (e: unknown) => setMsg(apiErrorMessage(e, "Aktion fehlgeschlagen."));

  const patch = useMutation({ mutationFn: ({ id, data }: { id: string; data: Parameters<typeof patchBattleWord>[1] }) => patchBattleWord(id, data), onSuccess: (w) => { setMsg(null); refresh(w); }, onError });
  const imgStatus = useMutation({
    mutationFn: ({ id, status, note }: { id: string; status: ImageStatus; note?: string }) => setImageStatus(id, status, note),
    onSuccess: (img) => { setMsg(null); refresh(selected ? { ...selected, image: img, status: img.status === "rejected" || img.status === "draft" ? (selected.status === "published" ? "draft" : selected.status) : selected.status } : undefined); },
    onError,
  });
  const [addId, setAddId] = useState("");
  const [addCat, setAddCat] = useState("");
  const add = useMutation({ mutationFn: () => addBattleWord(addId.trim(), addCat), onSuccess: (w) => { setAddId(""); setMsg(`${w.display} hinzugefügt (Entwurf).`); refresh(w); }, onError });

  const total = words.data?.total ?? 0;
  const pages = Math.max(1, Math.ceil(total / (words.data?.page_size ?? 30)));

  return (
    <div className="space-y-4" data-testid="admin-battle-words">
      <AdminCard>
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-5">
          <AdminInput placeholder="Suche (Wort / Übersetzung)" value={filters.q} onChange={(e) => setFilters({ ...filters, q: e.target.value, page: 1 })} />
          <AdminSelect value={filters.level} onChange={(e) => setFilters({ ...filters, level: e.target.value, page: 1 })} aria-label="Level">
            <option value="">Alle Level</option>{["A1", "A2", "B1", "B2", "C1"].map((l) => <option key={l}>{l}</option>)}
          </AdminSelect>
          <AdminSelect value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value, page: 1 })} aria-label="Status">
            <option value="">Alle Status</option>{["draft", "published", "disabled"].map((s) => <option key={s}>{s}</option>)}
          </AdminSelect>
          <AdminSelect value={filters.category} onChange={(e) => setFilters({ ...filters, category: e.target.value, page: 1 })} aria-label="Kategorie">
            <option value="">Alle Kategorien</option>{Object.entries(categories).map(([k, c]) => <option key={k} value={k}>{c.de}</option>)}
          </AdminSelect>
          <p className="self-center text-sm text-[var(--admin-text-secondary)]">{total} Wörter</p>
        </div>
        <form className="mt-3 flex flex-wrap gap-2" onSubmit={(e: FormEvent) => { e.preventDefault(); if (addId && addCat) add.mutate(); }}>
          <AdminInput className="max-w-[200px]" placeholder="Wörterbuch-ID, z. B. A1-12" value={addId} onChange={(e) => setAddId(e.target.value)} aria-label="Wörterbuch-ID" />
          <AdminSelect className="max-w-[220px]" value={addCat} onChange={(e) => setAddCat(e.target.value)} aria-label="Kategorie für neues Wort">
            <option value="">Kategorie…</option>{Object.entries(categories).map(([k, c]) => <option key={k} value={k}>{c.de}</option>)}
          </AdminSelect>
          <AdminButton type="submit" variant="secondary" disabled={!addId || !addCat || add.isPending}>Wort aus Wörterbuch hinzufügen</AdminButton>
        </form>
        {msg && <p role="status" className="mt-3 text-sm text-amber-300">{msg}</p>}
      </AdminCard>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5">
        {words.data?.items.map((w) => (
          <button key={w.id} type="button" onClick={() => setSelected(w)} data-testid="admin-battle-word"
                  className={cn("overflow-hidden rounded-2xl bg-[var(--admin-card)] text-left ring-1 transition hover:ring-[var(--admin-primary)]", selected?.id === w.id ? "ring-2 ring-[var(--admin-primary)]" : "ring-[var(--admin-border)]")}>
            {w.image ? <PrivateImage id={w.image.id} className="aspect-[4/3] w-full object-cover" /> : <div className="grid aspect-[4/3] place-items-center bg-[var(--admin-hover)] text-xs text-[var(--admin-text-muted)]">kein Bild</div>}
            <div className="p-3">
              <p className="truncate font-semibold text-[var(--admin-text-primary)]">{w.display}</p>
              <p className="truncate text-xs text-[var(--admin-text-secondary)]">{w.translation} · {categories[w.category]?.de ?? w.category} · {w.level}</p>
              <div className="mt-2 flex flex-wrap gap-1"><Badge s={w.status} />{w.image && <Badge s={w.image.status} />}</div>
            </div>
          </button>
        ))}
      </div>
      <div className="flex items-center justify-center gap-3 text-sm text-[var(--admin-text-secondary)]">
        <AdminButton size="sm" variant="ghost" disabled={filters.page <= 1} onClick={() => setFilters({ ...filters, page: filters.page - 1 })}>Zurück</AdminButton>
        {filters.page}/{pages}
        <AdminButton size="sm" variant="ghost" disabled={filters.page >= pages} onClick={() => setFilters({ ...filters, page: filters.page + 1 })}>Weiter</AdminButton>
      </div>

      {selected && (
        <WordDrawer word={selected} categories={categories} onClose={() => setSelected(null)} busy={patch.isPending || imgStatus.isPending}
                    onPatch={(data) => patch.mutate({ id: selected.id, data })} onImageStatus={(status, note) => selected.image && imgStatus.mutate({ id: selected.image.id, status, note })}
                    onChanged={(w) => { setMsg(null); refresh(w); }} onError={onError} />
      )}
    </div>
  );
}

function WordDrawer({ word, categories, onClose, busy, onPatch, onImageStatus, onChanged, onError }: {
  word: AdminWord;
  categories: Record<string, { de: string; uz: string }>;
  onClose: () => void;
  busy: boolean;
  onPatch: (d: { category?: string; status?: "draft" | "published" | "disabled" }) => void;
  onImageStatus: (s: ImageStatus, note?: string) => void;
  onChanged: (w: AdminWord) => void;
  onError: (e: unknown) => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [author, setAuthor] = useState("");
  const [license, setLicense] = useState("");
  const [source, setSource] = useState("");
  const [note, setNote] = useState("");
  const [q, setQ] = useState(word.lemma);
  const upload = useMutation({ mutationFn: () => uploadBattleImage(word.id, file!, { author, license, source_url: source }), onSuccess: (w) => { setFile(null); onChanged(w); }, onError });
  const search = useMutation({ mutationFn: () => searchCommons(q), onError });
  const imp = useMutation({ mutationFn: (title: string) => importCommons(word.id, title), onSuccess: onChanged, onError });
  const img = word.image;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/50" onClick={onClose}>
      <aside className="h-full w-full max-w-xl overflow-y-auto bg-[var(--admin-bg)] p-5 shadow-2xl ring-1 ring-[var(--admin-border)]" onClick={(e) => e.stopPropagation()} data-testid="admin-battle-drawer">
        <div className="mb-4 flex items-start justify-between gap-3">
          <div>
            <h2 className="text-xl font-bold text-[var(--admin-text-primary)]">{word.display}</h2>
            <p className="text-sm text-[var(--admin-text-secondary)]">{word.translation} · {word.level}</p>
          </div>
          <AdminButton size="sm" variant="ghost" onClick={onClose} aria-label="Schließen"><X size={16} /></AdminButton>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <AdminSelect value={word.category} onChange={(e) => onPatch({ category: e.target.value })} aria-label="Kategorie" disabled={busy}>
            {Object.entries(categories).map(([k, c]) => <option key={k} value={k}>{c.de}</option>)}
          </AdminSelect>
          <AdminSelect value={word.status} onChange={(e) => onPatch({ status: e.target.value as "draft" | "published" | "disabled" })} aria-label="Wortstatus" disabled={busy} data-testid="admin-word-status">
            <option value="draft">draft</option><option value="published">published</option><option value="disabled">disabled</option>
          </AdminSelect>
        </div>

        <h3 className="mb-2 mt-5 text-sm font-bold text-[var(--admin-text-primary)]">Aktuelles Bild</h3>
        {img ? (
          <AdminCard className="p-3">
            <PrivateImage id={img.id} className="max-h-72 w-full rounded-lg object-contain" />
            <dl className="mt-3 grid grid-cols-[110px_1fr] gap-x-2 gap-y-1 text-xs text-[var(--admin-text-secondary)]">
              <dt>Status</dt><dd><Badge s={img.status} /></dd>
              <dt>Quelle</dt><dd>{img.source}{img.source_url && <> · <a className="inline-flex items-center gap-1 text-[var(--admin-primary)] underline" href={img.source_url} target="_blank" rel="noopener noreferrer">Seite <ExternalLink size={11} /></a></>}</dd>
              <dt>Autor</dt><dd className="break-words">{img.author ?? "—"}</dd>
              <dt>Lizenz</dt><dd>{img.license ?? "—"}</dd>
              <dt>Größe</dt><dd>{img.width}×{img.height} · {Math.round(img.size_bytes / 1024)} KB</dd>
              {img.review_note && <><dt>Prüfnotiz</dt><dd className="break-words">{img.review_note}</dd></>}
            </dl>
            <AdminInput className="mt-3" placeholder="Prüfnotiz (optional)" value={note} onChange={(e) => setNote(e.target.value)} />
            <div className="mt-2 flex flex-wrap gap-2">
              <AdminButton size="sm" variant="secondary" disabled={busy} onClick={() => onImageStatus("verified", note)} data-testid="admin-image-verify">Geprüft (Verified)</AdminButton>
              <AdminButton size="sm" disabled={busy} onClick={() => onImageStatus("published", note)} data-testid="admin-image-publish">Veröffentlichen</AdminButton>
              <AdminButton size="sm" variant="danger" disabled={busy} onClick={() => onImageStatus("rejected", note)}>Ablehnen</AdminButton>
            </div>
            <p className="mt-2 text-[11px] text-[var(--admin-text-muted)]">Prüfen: zeigt das Bild eindeutig „{word.display}“? Kein Text mit dem Wort im Bild? Lizenz frei (CC0, PD, CC BY, CC BY-SA)?</p>
          </AdminCard>
        ) : <p className="text-sm text-[var(--admin-text-secondary)]">Noch kein Bild.</p>}

        <h3 className="mb-2 mt-5 text-sm font-bold text-[var(--admin-text-primary)]">Wikimedia Commons</h3>
        <form className="flex gap-2" onSubmit={(e) => { e.preventDefault(); search.mutate(); }}>
          <AdminInput value={q} onChange={(e) => setQ(e.target.value)} placeholder="Suchbegriff (englisch oft besser)" />
          <AdminButton type="submit" variant="secondary" disabled={search.isPending || q.length < 2}><Search size={15} />Suchen</AdminButton>
        </form>
        {search.data && (
          <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-3">
            {search.data.length === 0 && <p className="col-span-full text-xs text-[var(--admin-text-secondary)]">Keine frei lizenzierten Treffer.</p>}
            {search.data.map((c) => (
              <div key={c.title} className="overflow-hidden rounded-lg ring-1 ring-[var(--admin-border)]">
                {/* eslint-disable-next-line @next/next/no-img-element -- Commons thumbnail preview */}
                <img src={c.thumb_url} alt="" loading="lazy" className="aspect-square w-full object-cover" />
                <div className="p-1.5 text-[10px] text-[var(--admin-text-secondary)]">
                  <p className="truncate" title={c.author ?? ""}>{c.license} · {c.author ?? "?"}</p>
                  <AdminButton size="sm" className="mt-1 w-full" disabled={imp.isPending} onClick={() => imp.mutate(c.title)}>Übernehmen</AdminButton>
                </div>
              </div>
            ))}
          </div>
        )}

        <h3 className="mb-2 mt-5 text-sm font-bold text-[var(--admin-text-primary)]">Eigenes Bild hochladen</h3>
        <div className="space-y-2">
          <input type="file" accept="image/jpeg,image/png,image/webp" onChange={(e) => setFile(e.target.files?.[0] ?? null)} className="block w-full text-sm text-[var(--admin-text-secondary)]" aria-label="Bilddatei" />
          <div className="grid grid-cols-2 gap-2">
            <AdminInput placeholder="Autor / Rechteinhaber *" value={author} onChange={(e) => setAuthor(e.target.value)} />
            <AdminInput placeholder="Lizenz * (z. B. CC BY 4.0, Eigenes Foto)" value={license} onChange={(e) => setLicense(e.target.value)} />
          </div>
          <AdminInput placeholder="Quelle (URL, optional)" value={source} onChange={(e) => setSource(e.target.value)} />
          <AdminButton disabled={!file || author.length < 2 || license.length < 2 || upload.isPending} onClick={() => upload.mutate()}><ImagePlus size={15} />Hochladen (Entwurf)</AdminButton>
          <p className="text-[11px] text-[var(--admin-text-muted)]">JPEG/PNG/WebP bis 12 MB. Wird geprüft, als WebP gespeichert und privat abgelegt.</p>
        </div>
      </aside>
    </div>
  );
}
