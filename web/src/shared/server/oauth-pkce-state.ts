/**
 * PKCE `state`: signed blob carries `code_verifier` so Dashboard → localhost works
 * without Redis (same idea as tools-rizervox fallback).
 */
import { createHmac, hkdfSync, timingSafeEqual } from "node:crypto";

const PREFIX_V1 = "v1";
const PREFIX_V2 = "v2";
const EXP_SKEW_MS = 120_000;

function trimSecret(raw: string | undefined): string | undefined {
  if (!raw) return undefined;
  let s = raw.trim();
  if (
    (s.startsWith('"') && s.endsWith('"')) ||
    (s.startsWith("'") && s.endsWith("'"))
  ) {
    s = s.slice(1, -1).trim();
  }
  return s;
}

function deriveSigningKey(secret: string): Buffer {
  return Buffer.from(
    (hkdfSync(
      "sha256",
      Buffer.from(secret, "utf-8"),
      Buffer.from("oauth-pkce-state-salt", "utf-8"),
      Buffer.from("tools-project-pkce-state", "utf-8"),
      32,
    ) as unknown) as ArrayBuffer,
  );
}

function stateSigningKey(): Buffer {
  const explicit = trimSecret(process.env.OAUTH_PKCE_STATE_SECRET);
  if (explicit) {
    return deriveSigningKey(explicit);
  }
  throw new Error(
    "OAuth PKCE: set OAUTH_PKCE_STATE_SECRET so `state` can be signed.",
  );
}

function base64UrlDecode(s: string): Buffer {
  const pad = "=".repeat((4 - (s.length % 4)) % 4);
  const b64 = s.replace(/-/g, "+").replace(/_/g, "/") + pad;
  return Buffer.from(b64, "base64");
}

function canonicalForSig(v: string, exp: number): string {
  return JSON.stringify({ exp, v });
}

export function buildSignedOAuthState(verifier: string): string {
  const exp = Date.now() + 10 * 60 * 1000;
  const canon = canonicalForSig(verifier, exp);
  const sig = createHmac("sha256", stateSigningKey()).update(canon).digest();
  const sigB64 = Buffer.from(sig).toString("base64url");
  const bundle = JSON.stringify({ exp, v: verifier, sig: sigB64 });
  const blob = Buffer.from(bundle, "utf8").toString("base64url");
  return `${PREFIX_V2}.${blob}`;
}

function parseV2(state: string): { verifier: string } | null {
  const blob = state.slice(PREFIX_V2.length + 1);
  if (!blob || blob.length > 8192) return null;
  let parsed: { exp?: unknown; v?: unknown; sig?: unknown };
  try {
    parsed = JSON.parse(base64UrlDecode(blob).toString("utf8"));
  } catch {
    return null;
  }
  if (
    typeof parsed.v !== "string" ||
    typeof parsed.exp !== "number" ||
    typeof parsed.sig !== "string"
  ) {
    return null;
  }
  if (Date.now() > parsed.exp + EXP_SKEW_MS) {
    return null;
  }
  const canon = canonicalForSig(parsed.v, parsed.exp);
  let sig: Buffer;
  let expected: Buffer;
  try {
    sig = base64UrlDecode(parsed.sig);
    expected = createHmac("sha256", stateSigningKey()).update(canon).digest();
  } catch {
    return null;
  }
  if (sig.length !== expected.length || !timingSafeEqual(sig, expected)) {
    return null;
  }
  return { verifier: parsed.v };
}

function parseV1(state: string): { verifier: string } | null {
  const parts = state.split(".");
  if (parts.length !== 3 || parts[0] !== PREFIX_V1) return null;
  const [, sigB64, payloadB64] = parts;
  if (!sigB64 || !payloadB64) return null;
  let sig: Buffer;
  let expected: Buffer;
  try {
    sig = base64UrlDecode(sigB64);
    expected = createHmac("sha256", stateSigningKey())
      .update(payloadB64)
      .digest();
  } catch {
    return null;
  }
  if (sig.length !== expected.length || !timingSafeEqual(sig, expected)) {
    return null;
  }
  let parsed: { v?: unknown; exp?: unknown };
  try {
    parsed = JSON.parse(base64UrlDecode(payloadB64).toString("utf8"));
  } catch {
    return null;
  }
  if (typeof parsed.v !== "string" || typeof parsed.exp !== "number") {
    return null;
  }
  if (Date.now() > parsed.exp + EXP_SKEW_MS) {
    return null;
  }
  return { verifier: parsed.v };
}

export function parseSignedOAuthState(
  state: string | null,
): { verifier: string } | null {
  if (!state || state.length > 16384) return null;
  const s = state.trim();
  if (s.startsWith(`${PREFIX_V2}.`)) {
    return parseV2(s);
  }
  if (s.startsWith(`${PREFIX_V1}.`)) {
    return parseV1(s);
  }
  return null;
}
