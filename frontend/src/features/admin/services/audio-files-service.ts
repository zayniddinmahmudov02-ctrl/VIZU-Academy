import { api } from "@/src/services/api";

const FILES = "/api/v1/admin/audio-files";
const SLOTS = "/api/v1/admin/multilevel-audio";

export interface AudioFileInfo {
  id: string;
  kind: "ORIGINAL" | "TRIMMED";
  source_id: string | null;
  original_name: string | null;
  content_type: string;
  size_bytes: number;
  duration_ms: number | null;
  trim_start_ms: number | null;
  trim_end_ms: number | null;
  file_status: "ok" | "missing";
  created_at: string;
}

export type SlotStatus = "ok" | "missing" | "file_missing" | "external";

export interface MultilevelAudioSlot {
  content_id: string;
  teil_id: string;
  model_test_id: string;
  aufgabe_number: number;
  title: string;
  status: SlotStatus;
  audio: AudioFileInfo | null;
  original: AudioFileInfo | null;
  duration_ms: number | null;
  test_unpublished?: boolean;
  /** the Teil plays the ONE shared audio of its Hören section (Modelltest 1): no audio of its own */
  shared?: boolean;
}

/** The ONE audio of a Hören section in shared-audio mode (Modelltest 1). `exam_minutes` is the exam time — its own setting, independent of the audio length. */
export interface SharedAudioStatus {
  model_test_id: string;
  kompetenz_id: string;
  title: string;
  status: SlotStatus;
  audio: AudioFileInfo | null;
  original: AudioFileInfo | null;
  duration_ms: number | null;
  exam_minutes: number;
  teile: { teil_id: string; aufgabe_number: number; title: string; questions: number }[];
  test_unpublished?: boolean;
}

export interface MultilevelAudioTest {
  model_test_id: string;
  title: string;
  status: string;
  sort_order: number;
  slots: MultilevelAudioSlot[];
  shared?: SharedAudioStatus | null;
}

export interface MultilevelAudioOverview {
  level: string;
  tests: MultilevelAudioTest[];
  total: number;
  with_audio: number;
}

const AUDIO_ERRORS: Record<string, string> = {
  UNSUPPORTED_AUDIO: "Die Datei ist keine lesbare MP3-, WAV- oder M4A-Audiodatei.",
  AUDIO_TOO_LARGE: "Die Datei ist größer als 100 MB.",
  INVALID_RANGE: "Start und Ende passen nicht: Der Start muss vor dem Ende liegen, beide innerhalb der Aufnahme.",
  RANGE_TOO_SHORT: "Der gewählte Ausschnitt ist kürzer als 0,5 Sekunden.",
  AUDIO_PROCESSING_FAILED: "Das Audio konnte nicht gekürzt werden. Bitte eine andere Datei oder einen anderen Ausschnitt versuchen.",
  AUDIO_PROCESSING_TIMEOUT: "Das Kürzen hat zu lange gedauert. Bitte einen kürzeren Ausschnitt wählen.",
  AUDIO_FILE_MISSING: "Die Audiodatei fehlt auf dem Server.",
  AUDIO_TOOL_MISSING: "Die Audioverarbeitung ist auf dem Server nicht verfügbar.",
  AUDIO_NOT_FOUND: "Audio nicht gefunden.",
  SLOT_NOT_FOUND: "Dieser Audio-Platz gehört nicht zum Multilevel-Modelltest.",
  SHARED_AUDIO_TEST: "Dieser Modelltest nutzt ein gemeinsames Audio für alle Hören-Teile — bitte das gemeinsame Audio verwenden.",
  SHARED_AUDIO_NOT_AVAILABLE: "Dieser Modelltest hat kein gemeinsames Audio.",
};

/** A readable German message for an audio API error (the backend sends "CODE: text"). */
export function audioErrorMessage(err: unknown, fallback: string): string {
  const data = (err as { response?: { data?: { message?: unknown; detail?: unknown } } })?.response?.data;
  const raw = data?.message ?? data?.detail;
  if (typeof raw === "string") {
    const code = raw.split(":")[0].trim();
    if (AUDIO_ERRORS[code]) return AUDIO_ERRORS[code];
  }
  return fallback;
}

// ---- central audio files (Media Management + Multilevel Audio) ----

export async function uploadAudioOriginal(file: File, onProgress?: (percent: number) => void): Promise<AudioFileInfo> {
  const form = new FormData();
  form.append("file", file);
  return (await api.post<AudioFileInfo>(FILES, form, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: onProgress ? (e) => e.total && onProgress(Math.round((e.loaded / e.total) * 100)) : undefined,
  })).data;
}

export async function trimAudioFile(id: string, startMs: number, endMs: number): Promise<AudioFileInfo> {
  return (await api.post<AudioFileInfo>(`${FILES}/${id}/trim`, { start_ms: Math.round(startMs), end_ms: Math.round(endMs) })).data;
}

/** The stored file as a Blob (Bearer-authenticated; there is no public URL). */
export async function getAudioFileBlob(id: string): Promise<Blob> {
  return (await api.get(`${FILES}/${id}/file`, { responseType: "blob" })).data as Blob;
}

// ---- Multilevel Audio slots ----

export async function getMultilevelAudio(): Promise<MultilevelAudioOverview> {
  return (await api.get<MultilevelAudioOverview>(SLOTS)).data;
}

export async function getMultilevelSlot(contentId: string): Promise<MultilevelAudioSlot> {
  return (await api.get<MultilevelAudioSlot>(`${SLOTS}/slots/${contentId}`)).data;
}

/** Upload / replace: the slot plays this (already uploaded, possibly trimmed) file. */
export async function setMultilevelSlotAudio(contentId: string, audioFileId: string): Promise<MultilevelAudioSlot> {
  return (await api.put<MultilevelAudioSlot>(`${SLOTS}/slots/${contentId}`, { audio_file_id: audioFileId })).data;
}

export async function trimMultilevelSlot(contentId: string, startMs: number, endMs: number): Promise<MultilevelAudioSlot> {
  return (await api.post<MultilevelAudioSlot>(`${SLOTS}/slots/${contentId}/trim`, { start_ms: Math.round(startMs), end_ms: Math.round(endMs) })).data;
}

export async function deleteMultilevelSlotAudio(contentId: string): Promise<MultilevelAudioSlot> {
  return (await api.delete<MultilevelAudioSlot>(`${SLOTS}/slots/${contentId}`)).data;
}

// ---- shared audio of one Modelltest (Modelltest 1): one audio for all Hören Teile ----

export async function getMultilevelShared(modelTestId: string): Promise<SharedAudioStatus> {
  return (await api.get<SharedAudioStatus>(`${SLOTS}/shared/${modelTestId}`)).data;
}

/** Upload / replace: every Hören Teil of the Modelltest plays this (already uploaded, possibly trimmed) file. */
export async function setMultilevelSharedAudio(modelTestId: string, audioFileId: string): Promise<SharedAudioStatus> {
  return (await api.put<SharedAudioStatus>(`${SLOTS}/shared/${modelTestId}`, { audio_file_id: audioFileId })).data;
}

export async function deleteMultilevelSharedAudio(modelTestId: string): Promise<SharedAudioStatus> {
  return (await api.delete<SharedAudioStatus>(`${SLOTS}/shared/${modelTestId}`)).data;
}

export async function getMultilevelSharedBlob(modelTestId: string): Promise<Blob> {
  return (await api.get(`${SLOTS}/shared/${modelTestId}/file`, { responseType: "blob" })).data as Blob;
}

export async function getMultilevelSlotBlob(contentId: string): Promise<Blob> {
  return (await api.get(`${SLOTS}/slots/${contentId}/file`, { responseType: "blob" })).data as Blob;
}
