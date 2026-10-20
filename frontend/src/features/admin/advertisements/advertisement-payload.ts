import type {
  AdvertisementFieldError,
  AdvertisementLinkType,
  CreateAdvertisementPayload,
  InternalRoute,
} from "./advertisement-admin-service";

/** Werbung-Banner form state (what the inputs hold). Never sent as-is —
 * `buildAdvertisementPayload` maps it onto the backend contract. */
export interface AdvertisementFormState {
  title: string;
  description: string;
  /** Stored upload path from the media library ("/uploads/images/..."),
   * not the resolved preview URL. */
  image_url: string | null;
  link_type: AdvertisementLinkType;
  target_url: string;
  internal_route: string;
  internal_params: Record<string, string>;
  cta_text: string;
  is_active: boolean;
  priority: number;
  /** <input type="datetime-local"> value, browser-local time: "2026-10-02T21:45". */
  starts_at: string;
  ends_at: string;
}

export const EMPTY_ADVERTISEMENT_FORM: AdvertisementFormState = {
  title: "",
  description: "",
  image_url: null,
  link_type: "EXTERNAL",
  target_url: "",
  internal_route: "",
  internal_params: {},
  cta_text: "Mehr erfahren",
  is_active: false,
  priority: 0,
  starts_at: "",
  ends_at: "",
};

export const ADVERTISEMENT_FIELD_LABELS: Record<string, string> = {
  title: "Titel",
  description: "Beschreibung",
  image_url: "Bild",
  link_type: "Link-Typ",
  target_url: "Link",
  internal_route: "Studentenseite",
  internal_params: "Seitenparameter",
  cta_text: "CTA-Text",
  is_active: "Aktiv",
  priority: "Priorität",
  starts_at: "Startdatum",
  ends_at: "Enddatum",
};

/** datetime-local ("2026-10-02T21:45", the admin's local time) -> ISO 8601
 * in UTC ("2026-10-02T16:45:00.000Z" for UTC+5). The backend stores
 * timezone-aware datetimes, so the instant is exact. */
export function localInputToIso(local: string): string | null | "invalid" {
  if (!local) return null;
  const date = new Date(local);
  return Number.isNaN(date.getTime()) ? "invalid" : date.toISOString();
}

/** ISO from the API -> datetime-local value in the admin's local time. */
export function isoToLocalInput(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function isHttpUrl(value: string): boolean {
  if (/\s/.test(value)) return false;
  try {
    const url = new URL(value);
    return (url.protocol === "https:" || url.protocol === "http:") && url.hostname.includes(".") && !url.username && !url.password;
  } catch {
    return false;
  }
}

/** Form state -> CreateAdvertisementPayload, with the same checks the
 * backend runs, so obvious mistakes are explained before any request.
 * `routes` = the server's student-page whitelist (internal links). */
export function buildAdvertisementPayload(
  form: AdvertisementFormState,
  routes: InternalRoute[] = [],
): { ok: true; payload: CreateAdvertisementPayload } | { ok: false; errors: AdvertisementFieldError[] } {
  const errors: AdvertisementFieldError[] = [];
  const title = form.title.trim();
  const internal = form.link_type === "INTERNAL";
  const targetUrl = form.target_url.trim();
  const startsAt = localInputToIso(form.starts_at);
  const endsAt = localInputToIso(form.ends_at);
  let params: Record<string, string> = {};

  if (!title) errors.push({ field: "title", message: "Bitte einen Titel eingeben." });
  if (internal) {
    const route = routes.find((r) => r.key === form.internal_route);
    if (!route) {
      errors.push({ field: "internal_route", message: "Bitte eine Studentenseite aus der Liste wählen." });
    } else {
      params = Object.fromEntries(route.params.map((p) => [p.name, form.internal_params[p.name] ?? ""]));
      for (const p of route.params) {
        if (!p.choices.includes(params[p.name])) errors.push({ field: "internal_params", message: `Bitte „${p.name}“ wählen.` });
      }
    }
  } else if (!isHttpUrl(targetUrl)) {
    errors.push({ field: "target_url", message: "Bitte eine vollständige Adresse eingeben, z. B. https://www.vizu-deutsch.com/vizu-multilevel." });
  }
  if (!Number.isInteger(form.priority)) errors.push({ field: "priority", message: "Priorität muss eine ganze Zahl sein." });
  if (startsAt === "invalid") errors.push({ field: "starts_at", message: "Ungültiges Startdatum." });
  if (endsAt === "invalid") errors.push({ field: "ends_at", message: "Ungültiges Enddatum." });
  if (startsAt && endsAt && startsAt !== "invalid" && endsAt !== "invalid" && new Date(endsAt) <= new Date(startsAt)) {
    errors.push({ field: "ends_at", message: "Enddatum muss nach dem Startdatum liegen." });
  }
  if (errors.length) return { ok: false, errors };

  return {
    ok: true,
    payload: {
      title,
      description: form.description.trim() || null,
      image_url: form.image_url?.trim() || null,
      link_type: form.link_type,
      target_url: internal ? null : targetUrl,
      internal_route: internal ? form.internal_route : null,
      internal_params: internal ? params : null,
      cta_text: form.cta_text.trim() || "Mehr erfahren",
      is_active: form.is_active,
      priority: form.priority,
      starts_at: startsAt as string | null,
      ends_at: endsAt as string | null,
    },
  };
}
