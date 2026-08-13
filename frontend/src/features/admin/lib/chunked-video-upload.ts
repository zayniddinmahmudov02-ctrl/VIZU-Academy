import type { Video } from "../types/content.types";
import {
  completeVideoUpload,
  getVideoUploadStatus,
  initVideoUpload,
  uploadVideoChunk,
} from "../services/video-service";

export interface ChunkedUploadMetadata {
  lessonId: string;
  title: string;
  description?: string | null;
  durationSeconds?: number;
  orderIndex?: number;
  isPreview?: boolean;
  isPublished?: boolean;
  /** Set to swap an existing video's file instead of creating a new one. */
  replaceVideoId?: string | null;
}

export interface ChunkedUploadCallbacks {
  /** Cumulative bytes actually sent, out of the whole file — not
   *  per-chunk, so the UI progress bar advances smoothly across chunks
   *  instead of jumping back to 0% at the start of each one. */
  onProgress: (loadedBytes: number, totalBytes: number) => void;
  signal: AbortSignal;
}

const MAX_CHUNK_ATTEMPTS = 3;
const RETRY_BACKOFF_MS = 1000;

// Mirrors the backend's VIDEO_UPLOAD_SESSION_MAX_AGE_HOURS — an entry
// older than this is worth less than a wasted round-trip to check, since
// the server will have already swept the session and its temp chunks.
const RESUME_RECORD_MAX_AGE_MS = 24 * 60 * 60 * 1000;

interface ResumeRecord {
  uploadId: string;
  chunkSizeBytes: number;
  totalChunks: number;
  savedAt: number;
}

function storageKey(file: File, metadata: ChunkedUploadMetadata): string {
  // Same file re-selected (name+size+lastModified unchanged) for the same
  // lesson/replace target is treated as "the upload that got interrupted"
  // — the only signal available across a browser refresh, since a File
  // object itself can't survive one.
  const scope = metadata.replaceVideoId ? `replace:${metadata.replaceVideoId}` : `lesson:${metadata.lessonId}`;
  return `vizu-video-upload:${scope}:${file.name}:${file.size}:${file.lastModified}`;
}

function readResumeRecord(key: string): ResumeRecord | null {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return null;

    const record = JSON.parse(raw) as ResumeRecord;
    if (Date.now() - record.savedAt > RESUME_RECORD_MAX_AGE_MS) {
      localStorage.removeItem(key);
      return null;
    }
    return record;
  } catch {
    return null;
  }
}

function writeResumeRecord(key: string, record: ResumeRecord): void {
  try {
    localStorage.setItem(key, JSON.stringify(record));
  } catch {
    // Private-browsing / quota-full localStorage just means resume won't
    // work for this upload — not worth failing the upload itself over.
  }
}

function clearResumeRecord(key: string): void {
  try {
    localStorage.removeItem(key);
  } catch {
    // Nothing to clean up if this throws.
  }
}

function chunkRange(chunkNumber: number, chunkSizeBytes: number, fileSize: number): [number, number] {
  const start = chunkNumber * chunkSizeBytes;
  const end = Math.min(start + chunkSizeBytes, fileSize);
  return [start, end];
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/** Splits `file` into server-sized chunks and uploads each as its own
 *  request — every request stays well under the edge proxy's per-request
 *  limit no matter how large the finished video is (Cloudflare rejects a
 *  single request above ~50-99MB before it ever reaches the backend).
 *  Resumable: if the exact same file is uploaded again for the same
 *  lesson/replace target within 24h (e.g. after a refresh), already-
 *  uploaded chunks are skipped instead of re-sent. */
export async function uploadVideoChunked(
  file: File,
  metadata: ChunkedUploadMetadata,
  callbacks: ChunkedUploadCallbacks,
): Promise<Video> {
  const key = storageKey(file, metadata);
  const stored = readResumeRecord(key);

  let uploadId: string;
  let chunkSizeBytes: number;
  let totalChunks: number;
  let uploadedChunks = new Set<number>();

  const resumed = stored
    ? await getVideoUploadStatus(stored.uploadId).catch(() => null)
    : null;

  if (stored && resumed && resumed.total_chunks === stored.totalChunks) {
    uploadId = stored.uploadId;
    chunkSizeBytes = stored.chunkSizeBytes;
    totalChunks = stored.totalChunks;
    uploadedChunks = new Set(resumed.uploaded_chunks);
  } else {
    if (stored) clearResumeRecord(key);

    const init = await initVideoUpload({
      lesson_id: metadata.lessonId,
      title: metadata.title,
      description: metadata.description ?? null,
      duration_seconds: metadata.durationSeconds ?? 0,
      order_index: metadata.orderIndex ?? 1,
      is_preview: metadata.isPreview ?? false,
      is_published: metadata.isPublished ?? false,
      filename: file.name,
      content_type: file.type,
      total_size_bytes: file.size,
      replace_video_id: metadata.replaceVideoId ?? null,
    });

    uploadId = init.upload_id;
    chunkSizeBytes = init.chunk_size_bytes;
    totalChunks = init.total_chunks;

    writeResumeRecord(key, { uploadId, chunkSizeBytes, totalChunks, savedAt: Date.now() });
  }

  let completedBytes = 0;
  for (let n = 0; n < totalChunks; n++) {
    if (uploadedChunks.has(n)) {
      const [start, end] = chunkRange(n, chunkSizeBytes, file.size);
      completedBytes += end - start;
    }
  }
  callbacks.onProgress(completedBytes, file.size);

  for (let chunkNumber = 0; chunkNumber < totalChunks; chunkNumber++) {
    if (uploadedChunks.has(chunkNumber)) continue;

    const [start, end] = chunkRange(chunkNumber, chunkSizeBytes, file.size);
    const blob = file.slice(start, end);
    const chunkBytes = end - start;

    for (let attempt = 1; ; attempt++) {
      try {
        await uploadVideoChunk(uploadId, chunkNumber, totalChunks, blob, {
          signal: callbacks.signal,
          onUploadProgress: (event) => {
            callbacks.onProgress(completedBytes + (event.loaded ?? 0), file.size);
          },
        });
        break;
      } catch (err) {
        if (callbacks.signal.aborted || attempt >= MAX_CHUNK_ATTEMPTS) throw err;
        await sleep(attempt * RETRY_BACKOFF_MS);
      }
    }

    completedBytes += chunkBytes;
    callbacks.onProgress(completedBytes, file.size);
  }

  const video = await completeVideoUpload(uploadId);
  clearResumeRecord(key);

  return video;
}
