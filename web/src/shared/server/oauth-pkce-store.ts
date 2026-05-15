/**
 * PKCE verifier round-trip via signed OAuth `state` only (no Redis / API bridge).
 * Matches tools-rizervox fallback behaviour; sufficient for tools-project dev.
 */
import { buildSignedOAuthState, parseSignedOAuthState } from "./oauth-pkce-state";

function normalizeOAuthState(raw: string): string {
  let s = raw.trim();
  if (s.includes("%")) {
    try {
      s = decodeURIComponent(s);
    } catch {
      /* keep */
    }
  }
  return s.trim();
}

export async function buildOAuthPkceState(verifier: string): Promise<string> {
  return buildSignedOAuthState(verifier);
}

export async function resolvePkceVerifier(state: string): Promise<string | null> {
  const s = normalizeOAuthState(state);
  if (!s) return null;
  return parseSignedOAuthState(s)?.verifier ?? null;
}
