import { API_URL } from "@/src/constants/api";
import { api } from "@/services/api";

/** Latest published Android release as the public API returns it (no file path, no user data). */
export interface AppReleasePublic {
  platform: "android";
  version_name: string;
  version_code: number;
  min_android_version: string;
  release_notes: string;
  size_bytes: number;
  sha256: string;
  published_at: string | null;
  download_url: string;
  page_url: string;
}

export interface AppReleaseAdmin extends AppReleasePublic {
  id: string;
  status: "draft" | "published" | "archived";
  is_latest: boolean;
  original_name: string;
  signer_sha256: string | null;
  download_count: number;
  created_at: string;
  archived_at: string | null;
}

export interface AppReleaseList {
  releases: AppReleaseAdmin[];
  overview: {
    latest: AppReleaseAdmin | null;
    total_downloads: number;
    published: number;
    drafts: number;
    archived: number;
    package: string;
  };
}

const PUBLIC = "/api/v1/app";
const ADMIN = "/api/v1/admin/app-releases";

/** null = no release published yet (404 NO_APP_RELEASE) — the page then shows "coming soon". */
export async function getLatestRelease(): Promise<AppReleasePublic | null> {
  try {
    return (await api.get<AppReleasePublic>(`${PUBLIC}/releases/latest`)).data;
  } catch (err) {
    if ((err as { response?: { status?: number } })?.response?.status === 404) return null;
    throw err;
  }
}

/** Absolute APK / QR URLs (the API may live on another origin in development). */
export const apkUrl = (release: AppReleasePublic) => `${API_URL}${release.download_url}`;
export const downloadQrUrl = () => `${API_URL}${PUBLIC}/download-qr.svg`;

export const listReleases = async () => (await api.get<AppReleaseList>(ADMIN)).data;

export async function uploadRelease(file: File, releaseNotes: string, onProgress?: (percent: number) => void) {
  const form = new FormData();
  form.append("file", file);
  form.append("release_notes", releaseNotes);
  return (
    await api.post<AppReleaseAdmin>(ADMIN, form, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 10 * 60 * 1000,
      onUploadProgress: (e) => onProgress?.(e.total ? Math.round((e.loaded / e.total) * 100) : 0),
    })
  ).data;
}

export const updateReleaseNotes = async (id: string, release_notes: string) =>
  (await api.patch<AppReleaseAdmin>(`${ADMIN}/${id}`, { release_notes })).data;
export const publishRelease = async (id: string) => (await api.post<AppReleaseAdmin>(`${ADMIN}/${id}/publish`)).data;
export const archiveRelease = async (id: string) => (await api.post<AppReleaseAdmin>(`${ADMIN}/${id}/archive`)).data;
export const deleteDraftRelease = async (id: string) => {
  await api.delete(`${ADMIN}/${id}`);
};

/** Admin download of any release file (authenticated, so fetched as a blob). */
export async function downloadReleaseFile(release: AppReleaseAdmin) {
  const res = await api.get<Blob>(`${ADMIN}/${release.id}/file`, { responseType: "blob" });
  const url = URL.createObjectURL(res.data);
  const a = document.createElement("a");
  a.href = url;
  a.download = `VIZU-DEUTSCH-${release.version_name}.apk`;
  a.click();
  URL.revokeObjectURL(url);
}
