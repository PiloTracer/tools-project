type ApiErrorBody = {
  detail?: string | Array<{ msg?: string; type?: string }>;
  error?: string;
};

export type ApiResult<T> = { ok: true; data: T } | { ok: false; error: string };

function extractDetail(body: unknown): string | undefined {
  if (!body || typeof body !== "object") return undefined;
  const b = body as ApiErrorBody;
  if (typeof b.detail === "string") return b.detail;
  if (Array.isArray(b.detail)) {
    return b.detail
      .map((e) => e.msg ?? e.type)
      .filter(Boolean)
      .join("; ");
  }
  if (typeof b.error === "string") return b.error;
  return undefined;
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
