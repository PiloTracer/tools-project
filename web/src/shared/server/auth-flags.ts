/** Parse AUTH_* env flags — unset defaults to `defaultValue` (hybrid dev: both on). */
export function parseAuthFlag(
  raw: string | undefined,
  defaultValue: boolean,
): boolean {
  const v = raw?.trim().toLowerCase();
  if (v === "0" || v === "false" || v === "no" || v === "off") return false;
  if (v === "1" || v === "true" || v === "yes" || v === "on") return true;
  return defaultValue;
}

export function oauthEnabledServer(): boolean {
  return parseAuthFlag(process.env.AUTH_OAUTH_ENABLED, true);
}

export function localEnabledServer(): boolean {
  return parseAuthFlag(process.env.AUTH_LOCAL_ENABLED, true);
}
