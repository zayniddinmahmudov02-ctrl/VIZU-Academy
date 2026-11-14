/** Time helpers of the audio trimmer (milliseconds <-> "m:ss.s"). Pure, unit-tested. */

export function formatMs(ms: number): string {
  const safe = Math.max(0, Math.round(ms));
  const minutes = Math.floor(safe / 60000);
  const seconds = (safe % 60000) / 1000;
  return `${String(minutes).padStart(2, "0")}:${seconds.toFixed(1).padStart(4, "0")}`;
}

/** "1:20", "01:20.5", "80" or "80,5" -> ms; null when it is not a time. */
export function parseTime(text: string): number | null {
  const value = text.trim().replace(",", ".");
  if (!value) return null;
  const parts = value.split(":");
  if (parts.length > 3 || parts.some((p) => !/^\d+(\.\d+)?$/.test(p))) return null;
  const numbers = parts.map(Number);
  const seconds = numbers.reduce((total, n) => total * 60 + n, 0);
  return Number.isFinite(seconds) ? Math.round(seconds * 1000) : null;
}

export const MIN_TRIM_MS = 500;

/** Keeps a selection inside [0, duration] with at least MIN_TRIM_MS between start and end. */
export function clampRange(startMs: number, endMs: number, durationMs: number, moved: "start" | "end"): [number, number] {
  let start = Math.min(Math.max(0, startMs), durationMs);
  let end = Math.min(Math.max(0, endMs), durationMs);
  if (end - start < MIN_TRIM_MS) {
    if (moved === "start") start = Math.max(0, end - MIN_TRIM_MS);
    else end = Math.min(durationMs, start + MIN_TRIM_MS);
  }
  return [Math.round(start), Math.round(end)];
}

/** Waveform peaks (0..1) of decoded channel data in `buckets` buckets. */
export function peaks(samples: Float32Array, buckets: number): number[] {
  const size = Math.max(1, Math.floor(samples.length / buckets));
  const out: number[] = [];
  for (let b = 0; b < buckets; b += 1) {
    let max = 0;
    const from = b * size;
    const to = Math.min(samples.length, from + size);
    for (let i = from; i < to; i += 1) max = Math.max(max, Math.abs(samples[i]));
    out.push(max);
  }
  const top = Math.max(...out, 0.0001);
  return out.map((v) => v / top);
}
