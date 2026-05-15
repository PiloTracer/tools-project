/**
 * OAuth kick-off — authorization code + PKCE (tools-dashboard IdP).
 */
import { NextRequest, NextResponse } from "next/server";
import { absoluteUrl } from "@/shared/server/app-origin";
import { oauthEnabledServer } from "@/shared/server/auth-flags";
import { buildOAuthPkceState } from "@/shared/server/oauth-pkce-store";

function base64URLEncode(buf: Uint8Array): string {
  return btoa(String.fromCharCode(...buf))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
}

async function sha256(plain: string): Promise<ArrayBuffer> {
  const encoder = new TextEncoder();
  return crypto.subtle.digest("SHA-256", encoder.encode(plain));
}

function generateRandomString(length: number): string {
  const arr = new Uint8Array(length);
  crypto.getRandomValues(arr);
  return base64URLEncode(arr).slice(0, length);
}

export async function GET(req: NextRequest) {
  if (!oauthEnabledServer()) {
    return NextResponse.redirect(
      absoluteUrl(req, "/login?error=oauth_disabled"),
    );
  }

  const clientId = process.env.OAUTH_CLIENT_ID;
  if (!clientId) {
    return new NextResponse(
      "OAUTH_CLIENT_ID is not configured. Copy .env.example to .env and register the OAuth client.",
      { status: 500 },
    );
  }

  const verifier = generateRandomString(64);
  const challengeBuf = await sha256(verifier);
  const challenge = base64URLEncode(new Uint8Array(challengeBuf));
  let state: string;
  try {
    state = await buildOAuthPkceState(verifier);
  } catch (e) {
    const msg = e instanceof Error ? e.message : "OAuth PKCE state misconfigured";
    return new NextResponse(msg, { status: 500 });
  }

  const authorizationEndpoint =
    process.env.NEXT_PUBLIC_OAUTH_AUTHORIZATION_ENDPOINT ||
    "https://dev.aiepic.app/oauth/authorize";
  const redirectUri = process.env.OAUTH_REDIRECT_URI;
  const scopes = process.env.OAUTH_SCOPES || "profile email";

  const authUrl = new URL(authorizationEndpoint);
  authUrl.searchParams.set("response_type", "code");
  authUrl.searchParams.set("client_id", clientId);
  if (redirectUri) authUrl.searchParams.set("redirect_uri", redirectUri);
  authUrl.searchParams.set("scope", scopes);
  authUrl.searchParams.set("state", state);
  authUrl.searchParams.set("code_challenge", challenge);
  authUrl.searchParams.set("code_challenge_method", "S256");

  const res = NextResponse.redirect(authUrl.toString());
  res.headers.set("Cache-Control", "no-store, no-cache, must-revalidate");
  res.headers.set("Pragma", "no-cache");
  return res;
}
