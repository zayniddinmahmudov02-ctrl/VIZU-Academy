/** Batch import of A2 audio files — the parts without React, unit-tested in
 *  frontend/tests/unit/a2-audio-import.test.mjs. The server checks every
 *  file again (content, MIME type, size, duplicates); this only spares the
 *  admin an upload that cannot succeed and sorts the results. */

export const A2_MAX_BYTES = 100 * 1024 * 1024; // backend A2_AUDIO_MAX_BYTES default
export const A2_EXTENSIONS = ["mp3", "m4a"];
export const A2_ACCEPT = ".mp3,.m4a,audio/mpeg,audio/mp4,audio/x-m4a";

export type ImportOutcome = "success" | "duplicate" | "error";

export interface ImportResult {
  name: string;
  outcome: ImportOutcome;
  /** the new library entry (success) or the existing one (duplicate) */
  assetId: string | null;
  message: string | null;
  /** success, but not linked to a Hören task yet */
  unlinked: boolean;
}

/** null = fine to send; otherwise why the file is not sent. */
export function precheck(name: string, size: number, maxBytes = A2_MAX_BYTES): string | null {
  const ext = name.includes(".") ? name.split(".").pop()!.toLowerCase() : "";
  if (!A2_EXTENSIONS.includes(ext)) return `Nur ${A2_EXTENSIONS.map((e) => e.toUpperCase()).join(" oder ")} ist zulässig.`;
  if (size === 0) return "Die Datei ist leer.";
  if (size > maxBytes) return `Die Datei überschreitet ${Math.round(maxBytes / 1024 / 1024)} MB.`;
  if (/^\s*(a1|b1|b2|c1)\b/i.test(name)) return "Der Dateiname nennt ein anderes Niveau als A2.";
  return null;
}

/** Reads the server's answer for one file (axios error or the created asset). */
export function classify(name: string, outcome: { asset?: { id: string; linked: unknown } | null; error?: unknown }): ImportResult {
  if (outcome.asset) return { name, outcome: "success", assetId: outcome.asset.id, message: null, unlinked: !outcome.asset.linked };
  const data = (outcome.error as { response?: { status?: number; data?: { message?: unknown; detail?: unknown } } })?.response;
  const payload = data?.data?.message ?? data?.data?.detail;
  if (payload && typeof payload === "object" && (payload as { code?: string }).code === "DUPLICATE") {
    const dup = payload as { existing_id?: string; existing_filename?: string };
    return { name, outcome: "duplicate", assetId: dup.existing_id ?? null, unlinked: false,
             message: dup.existing_filename ? `Schon vorhanden als „${dup.existing_filename}“.` : "Diese Datei ist schon in der Bibliothek." };
  }
  if (typeof payload === "string" && payload) return { name, outcome: "error", assetId: null, message: payload, unlinked: false };
  if (!data) return { name, outcome: "error", assetId: null, message: "Keine Verbindung zum Server.", unlinked: false };
  return { name, outcome: "error", assetId: null, message: `Upload fehlgeschlagen (HTTP ${data.status ?? "?"}).`, unlinked: false };
}

export function summarize(results: ImportResult[]) {
  return {
    total: results.length,
    success: results.filter((r) => r.outcome === "success").length,
    duplicate: results.filter((r) => r.outcome === "duplicate").length,
    error: results.filter((r) => r.outcome === "error").length,
    unlinked: results.filter((r) => r.outcome === "success" && r.unlinked).length,
  };
}
