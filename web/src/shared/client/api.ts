type ApiErrorBody = {
  detail?: string | Array<{ msg?: string; type?: string; loc?: unknown[] }>;
  error?: string;
};

export type ApiResult<T> = { ok: true; data: T } | { ok: false; error: string };

/**
 * Turns a parsed error body into a displayable string.
 *
 * FastAPI answers validation failures (422) with `detail` as an **array of
 * objects** (`{type, loc, msg, input, ctx}`). Rendering that array as a React
 * child throws React error #31 and unmounts the whole page, so every caller
 * that displays an API error must normalize it first.
 */
export function extractDetail(body: unknown): string | undefined {
  if (!body || typeof body !== "object") return undefined;
  const b = body as ApiErrorBody;
  if (typeof b.detail === "string") return b.detail;
  if (Array.isArray(b.detail)) {
    return b.detail
      .map((e) => {
        const where = Array.isArray(e?.loc)
          ? e.loc.filter((p) => p !== "body" && p !== "query" && p !== "path").join(".")
          : "";
        const what = e?.msg ?? e?.type ?? "invalid value";
        return where ? `${where}: ${what}` : what;
      })
      .filter(Boolean)
      .join("; ");
  }
  if (typeof b.error === "string") return b.error;
  return undefined;
}

/** Never throws. Turns any error body (already parsed) into a displayable string. */
export function errorTextFromBody(body: unknown, status?: number): string {
  const detail = extractDetail(body);
  if (detail) return detail;
  if (typeof body === "string" && body.trim()) return body.trim();
  if (body !== undefined && body !== null) {
    try {
      const s = JSON.stringify(body);
      if (s && s !== "{}" && s !== "null") {
        return s.length > 300 ? `${s.slice(0, 300)}…` : s;
      }
    } catch {
      /* not serializable */
    }
  }
  return status ? `Error ${status}` : "Request failed";
}

/** Never throws. Parses an error response body (raw text) into a displayable string. */
export function apiErrorMessage(text: string, status?: number): string {
  if (text) {
    try {
      return errorTextFromBody(JSON.parse(text), status);
    } catch {
      /* body is not JSON */
    }
    if (text.trim()) return text.trim();
  }
  return status ? `Error ${status}` : "Request failed";
}

/**
 * Hard-navigate to the signin page, preserving the current location so the
 * user returns to it after signing in again. Used when the session has
 * expired (API answers 401). A full navigation (not router.push) flushes the
 * stale RSC cache that still holds pre-expiry page data.
 */
export function redirectToLogin(): void {
  if (typeof window === "undefined") return;
  const next = window.location.pathname + window.location.search;
  window.location.assign(`/login?next=${encodeURIComponent(next)}`);
}

/**
 * Thin fetch wrapper that normalizes error handling.
 * On success returns `{ ok: true, data: T }`.
 * On failure returns `{ ok: false, error: string }` (network, HTTP error, or parse failure).
 * On 401 the session has expired: redirects to the signin page.
 */
export async function apiRequest<T = unknown>(
  url: string,
  init?: RequestInit,
): Promise<ApiResult<T>> {
  let r: Response;
  try {
    r = await fetch(url, init);
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : "Network error" };
  }

  if (r.status === 401) {
    redirectToLogin();
    return { ok: false, error: "Session expired — please sign in again" };
  }

  if (!r.ok) {
    const text = await r.text().catch(() => "");
    let detail: string | undefined;
    try {
      detail = extractDetail(JSON.parse(text));
    } catch {
      /* body is not JSON */
    }
    return { ok: false, error: detail || text || `Error ${r.status}` };
  }

  if (r.status === 204) return { ok: true, data: null as T };

  try {
    const data = (await r.json()) as T;
    return { ok: true, data };
  } catch {
    return { ok: false, error: "Invalid response" };
  }
}

/**
 * Convenience helper: calls apiRequest and toasts the error automatically.
 * Returns data on success, `null` on failure.
 */
export async function apiWithToast<T = unknown>(
  url: string,
  init?: RequestInit,
): Promise<T | null> {
  const result = await apiRequest<T>(url, init);
  if (!result.ok) {
    const { toast } = await import("@/components/Toast");
    toast(result.error, "error");
    return null;
  }
  return result.data;
}
