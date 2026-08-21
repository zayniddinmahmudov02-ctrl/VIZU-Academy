"""Read-only Gemini model discovery/availability check — no writes, no
side effects. Confirms which models the configured GEMINI_API_KEY can
actually reach and use for generateContent, rather than guessing.

Never prints the API key itself.

Run from the `backend/` directory:

    python -m app.scripts.check_gemini_models
    python -m app.scripts.check_gemini_models --test gemini-flash-latest,gemini-flash-lite-latest

Without --test, it only lists models (one read-only ListModels call).
With --test, it additionally sends one trivial generateContent request
per listed model to confirm it's genuinely usable (not just listed) --
this costs a small amount of real API quota per model tested, so it's
opt-in.
"""

import argparse
import json
import sys
import urllib.error
import urllib.request

from app.core.config import settings

LIST_MODELS_URL = "https://generativelanguage.googleapis.com/v1beta/models?key={key}"
GENERATE_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"


def list_models(api_key: str) -> list[dict]:
    url = LIST_MODELS_URL.format(key=api_key)
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        print(f"ListModels failed: HTTP {exc.code}")
        print(exc.read().decode("utf-8", errors="ignore")[:500])
        sys.exit(1)
    except urllib.error.URLError as exc:
        print(f"ListModels failed: {exc.reason}")
        sys.exit(1)

    return data.get("models", [])


def test_generate(model_name: str, api_key: str) -> tuple[bool, str]:
    """One trivial live call -- confirms the model is genuinely callable
    with this key, not just present in the ListModels response."""
    url = GENERATE_URL.format(model=model_name, key=api_key)
    payload = json.dumps({"contents": [{"parts": [{"text": "Reply with exactly one word: OK"}]}]}).encode("utf-8")
    request = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
        text = body["candidates"][0]["content"]["parts"][0]["text"].strip()
        return True, text[:50]
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        return False, f"HTTP {exc.code}: {detail[:150]}"
    except urllib.error.URLError as exc:
        return False, f"network error: {exc.reason}"
    except (KeyError, IndexError):
        return False, "unexpected response shape"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--test", type=str, default="", help="Comma-separated model names to live-test.")
    args = parser.parse_args()

    if not settings.GEMINI_API_KEY:
        print("GEMINI_API_KEY is not configured in this environment.")
        sys.exit(1)

    print(f"Currently configured GEMINI_MODEL (primary): {settings.GEMINI_MODEL}")
    print(f"Currently configured GEMINI_FALLBACK_MODEL:  {settings.GEMINI_FALLBACK_MODEL or '(none)'}")
    print()

    models = list_models(settings.GEMINI_API_KEY)
    supporting = [m for m in models if "generateContent" in m.get("supportedGenerationMethods", [])]

    print(f"Total models listed: {len(models)}")
    print(f"Models supporting generateContent: {len(supporting)}")
    print()
    for m in supporting:
        name = m.get("name", "").removeprefix("models/")
        print(f"  {name}  ({m.get('displayName', '')})")

    primary_short = settings.GEMINI_MODEL
    primary_listed = any(m.get("name", "").removeprefix("models/") == primary_short for m in supporting)
    print()
    print(f"Primary model '{primary_short}' listed as generateContent-capable: {primary_listed}")

    if args.test:
        print()
        print("=== Live generateContent test ===")
        for name in [n.strip() for n in args.test.split(",") if n.strip()]:
            ok, detail = test_generate(name, settings.GEMINI_API_KEY)
            status = "SUCCESS" if ok else "FAILED"
            print(f"  {name}: {status} -- {detail}")


if __name__ == "__main__":
    main()
