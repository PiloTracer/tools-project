/**
 * OAuth configuration — env getters aligned with tools-dashboard / org apps.
 */
const _required = (name: string): string => {
  const v = process.env[name];
  if (!v) throw new Error(`${name} is required`);
  return v;
};

export const getAuthorizationEndpoint = (): string =>
  process.env.NEXT_PUBLIC_OAUTH_AUTHORIZATION_ENDPOINT ||
  "https://dev.aiepic.app/oauth/authorize";

export const getOAuthClientId = (): string => _required("OAUTH_CLIENT_ID");

export const getOAuthClientSecret = (): string | undefined =>
  process.env.OAUTH_CLIENT_SECRET || undefined;

export const getOAuthRedirectUri = (): string =>
  _required("OAUTH_REDIRECT_URI");

export const getOAuthScopes = (): string =>
  process.env.OAUTH_SCOPES || "profile email";

export const getTokenEndpoint = (): string =>
  _required("OAUTH_TOKEN_ENDPOINT");

export const getUserInfoEndpoint = (): string =>
  _required("OAUTH_USER_INFO_ENDPOINT");
