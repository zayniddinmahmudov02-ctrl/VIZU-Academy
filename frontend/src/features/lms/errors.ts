import { ApiError } from "@/lib/api";

export interface LmsErrorInfo {
  status: number | null;
  /** translation keys */
  titleKey: string;
  hintKey: string;
  /** a retry can help (network / 5xx); 4xx answers won't change by retrying */
  retry: boolean;
  premium: boolean;
  requestId: string | null;
}

function message(err: ApiError): string | null {
  const data = err.data as { message?: unknown; detail?: unknown } | null;
  const value = data?.message ?? data?.detail;
  return typeof value === "string" ? value : null;
}

/** Maps a failed LMS / content request to a message the student understands —
 * never hides the status: 401/403/404/5xx each get their own text. */
export function describeLmsError(err: unknown): LmsErrorInfo {
  if (!(err instanceof ApiError)) {
    return { status: null, titleKey: "lms.errorNetworkTitle", hintKey: "lms.errorNetworkHint", retry: true, premium: false, requestId: null };
  }
  const base = { status: err.status, retry: false, premium: false, requestId: err.requestId };
  if (err.status === 401) return { ...base, titleKey: "lms.errorSessionTitle", hintKey: "lms.errorSessionHint" };
  if (err.status === 403) {
    const code = message(err);
    if (code === "PREMIUM_REQUIRED") return { ...base, premium: true, titleKey: "lms.lockPremiumTitle", hintKey: "lms.lockPremiumHint" };
    if (code === "LESSON_LOCKED") return { ...base, titleKey: "lms.lockLockedTitle", hintKey: "lms.lockLockedHint" };
    return { ...base, titleKey: "lms.errorForbiddenTitle", hintKey: "lms.errorForbiddenHint" };
  }
  if (err.status === 404) return { ...base, titleKey: "lms.errorNotFoundTitle", hintKey: "lms.errorNotFoundHint" };
  if (err.status >= 500) return { ...base, retry: true, titleKey: "lms.errorServerTitle", hintKey: "lms.errorServerHint" };
  return { ...base, retry: true, titleKey: "lms.errorServerTitle", hintKey: "lms.errorServerHint" };
}

/** TanStack Query retry policy: never re-ask on a 4xx. */
export function retryUnlessClientError(failureCount: number, err: unknown): boolean {
  if (err instanceof ApiError && err.status >= 400 && err.status < 500) return false;
  return failureCount < 2;
}
