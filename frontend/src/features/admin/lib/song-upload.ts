/* Pure helpers of the Musik bulk upload (no React, no project imports: unit-tested with node --test). */

export const MAX_FILES = 500;
/** files sent at the same time: enough to keep the line busy, few enough for the server (each request writes one file, hashes it, nothing else) */
export const CONCURRENCY = 3;
export const AUDIO_EXTENSIONS = ["mp3", "wav", "m4a", "aac", "ogg", "flac"];

export type UploadState = "hashing" | "wait" | "dup" | "up" | "done" | "error" | "missing";

export interface RowLike {
  key: string;
  fileId: string;
  name: string;
  size: number;
  sha: string | null;
  state: UploadState;
  percent: number;
  processing?: string | null;
}

/** The same file on this computer (re-selected after a reload): name + size + last change. */
export const fileIdOf = (f: { name: string; size: number; lastModified: number }) => `${f.name}|${f.size}|${f.lastModified}`;

export const isAudioName = (name: string) => AUDIO_EXTENSIONS.includes((name.split(".").pop() ?? "").toLowerCase());

/** "SONG_DUPLICATE: <uuid> <title>" (the server's 409) → the existing song. */
export function parseDuplicate(message: string | null | undefined): { id: string; title: string } | null {
  const m = /SONG_DUPLICATE:\s*([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\s*(.*)$/i.exec(message ?? "");
  return m ? { id: m[1], title: m[2].trim() } : null;
}

/** Rows whose file content (hash) already appears in an EARLIER row of the list: the same file chosen twice. */
export function localDuplicates(rows: readonly Pick<RowLike, "key" | "sha">[]): Map<string, string> {
  const first = new Map<string, string>();
  const dups = new Map<string, string>();
  for (const r of rows) {
    if (!r.sha) continue;
    const seen = first.get(r.sha);
    if (seen) dups.set(r.key, seen);
    else first.set(r.sha, r.key);
  }
  return dups;
}

/** Keys of rows that share a file NAME with another row (other content) — shown as a hint, never removed. */
export function sameNames(rows: readonly Pick<RowLike, "key" | "name" | "sha">[]): Set<string> {
  const byName = new Map<string, Pick<RowLike, "key" | "name" | "sha">[]>();
  for (const r of rows) byName.set(r.name.toLowerCase(), [...(byName.get(r.name.toLowerCase()) ?? []), r]);
  const out = new Set<string>();
  for (const group of byName.values()) {
    if (group.length < 2) continue;
    const contents = new Set(group.map((r) => r.sha ?? r.key));
    if (contents.size > 1) group.forEach((r) => out.add(r.key));
  }
  return out;
}

export interface Summary {
  total: number; done: number; failed: number; dups: number; uploading: number; waiting: number; missing: number; remaining: number;
  bytesTotal: number; bytesDone: number; percent: number; processing: number;
}

/** The numbers of the progress panel. `remaining` = what still has to go up (waiting + uploading + needing the file again);
 * `percent` = bytes on the server out of the bytes to send (duplicates are not sent, so they do not count). */
export function summarize(rows: readonly RowLike[]): Summary {
  let done = 0, failed = 0, dups = 0, uploading = 0, waiting = 0, missing = 0, bytesTotal = 0, bytesDone = 0, processing = 0;
  for (const r of rows) {
    if (r.state === "dup") { dups += 1; continue; }
    bytesTotal += r.size;
    if (r.state === "done") { done += 1; bytesDone += r.size; if (r.processing === "PENDING" || r.processing === "PROCESSING") processing += 1; }
    else if (r.state === "error") failed += 1;
    else if (r.state === "up") { uploading += 1; bytesDone += (r.size * Math.min(100, Math.max(0, r.percent))) / 100; }
    else if (r.state === "missing") missing += 1;
    else waiting += 1; // wait + hashing
  }
  const percent = bytesTotal ? Math.floor((bytesDone / bytesTotal) * 100) : 0;
  return { total: rows.length, done, failed, dups, uploading, waiting, missing, remaining: waiting + uploading + missing, bytesTotal, bytesDone, percent, processing };
}

/** After a reload the files are gone (browsers never keep them): finished rows stay finished, everything else needs its file again. */
export function restoreState(state: UploadState): UploadState {
  return state === "done" || state === "dup" ? state : "missing";
}

/** How many of the picked files can still be taken (the list holds at most MAX_FILES). */
export const room = (current: number) => Math.max(0, MAX_FILES - current);
