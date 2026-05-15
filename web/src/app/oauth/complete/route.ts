/**
 * OAuth callback — exchange code for tokens; set session cookies.
 * Pattern aligned with tools-rizervox (simplified PKCE: signed state only).
 */
import { NextRequest, NextResponse } from "next/server";
import {
  getOAuthClientId,
  getOAuthClientSecret,
  getOAuthRedirectUri,
  getTokenEndpoint,
  getUserInfoEndpoint,
} from "@/shared/server/oauth-config";
import { oauthServerFetch } from "@/shared/server/oauth-fetch";
import { absoluteUrl } from "@/shared/server/app-origin";
import { oauthEnabledServer } from "@/shared/server/auth-flags";
import { resolvePkceVerifier } from "@/shared/server/oauth-pkce-store";

const COOKIE = {
  access: process.env.SESSION_COOKIE_NAME || "prj_auth",
  refresh: process.env.REFRESH_COOKIE_NAME || "prj_refresh",
};

export async function GET(req: NextRequest) {
  const url = req.nextUrl;

  if (!oauthEnabledServer()) {
    return NextResponse.redirect(
      absoluteUrl(req, "/login?error=oauth_disabled"),
    );
  }

  const oauthError = url.searchParams.get("error");
  if (oauthError) {
    const q = new URLSearchParams({
      error: "oauth_provider",
      oauth_error: oauthError,
    });
    const desc = url.searchParams.get("error_description");
    if (desc) q.set("oauth_error_description", desc.slice(0, 600));
    return NextResponse.redirect(absoluteUrl(req, `/login?${q}`));
  }

  const code = url.searchParams.get("code");
  const receivedState = url.searchParams.get("state");

  if (!receivedState) {
    return NextResponse.redirect(absoluteUrl(req, "/login?error=no_state"));
  }
  const storedVerifier = await resolvePkceVerifier(receivedState);
  if (!storedVerifier) {
    const isExternalLaunchState = /^[a-fA-F0-9]{48,}$/.test(receivedState);
    if (isExternalLaunchState) {
      return NextResponse.redirect(absoluteUrl(req, "/sign-in"));
    }
    return NextResponse.redirect(
      absoluteUrl(req, "/login?error=oauth_state_invalid"),
    );
  }
  if (!code) {
    return NextResponse.redirect(absoluteUrl(req, "/login?error=no_code"));
  }

  const secret = getOAuthClientSecret()?.trim();
  if (!secret) {
    return NextResponse.redirect(absoluteUrl(req, "/login?error=oauth_config"));
  }

  const body: Record<string, string> = {
    grant_type: "authorization_code",
    code,
    redirect_uri: getOAuthRedirectUri(),
    client_id: getOAuthClientId(),
    client_secret: secret,
    code_verifier: storedVerifier,
  };

  const tokenResp = await oauthServerFetch(getTokenEndpoint(), {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams(body),
  });
  if (!tokenResp.ok) {
    return NextResponse.redirect(
      absoluteUrl(req, "/login?error=token_exchange"),
    );
  }
  const tokens = (await tokenResp.json()) as {
    access_token: string;
    refresh_token: string;
    expires_in: number;
    scope: string;
  };

  const ui = await oauthServerFetch(getUserInfoEndpoint(), {
    headers: { Authorization: `Bearer ${tokens.access_token}` },
  });
  if (!ui.ok) {
    return NextResponse.redirect(absoluteUrl(req, "/login?error=userinfo"));
  }

  const dest = absoluteUrl(req, "/projects");
  const res = NextResponse.redirect(dest);
  res.cookies.set(COOKIE.access, tokens.access_token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: tokens.expires_in,
  });
  res.cookies.set(COOKIE.refresh, tokens.refresh_token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 30 * 24 * 60 * 60,
  });
  return res;
}
