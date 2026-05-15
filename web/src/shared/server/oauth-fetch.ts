/** Server-side fetch to IdP token/userinfo endpoints. */
export async function oauthServerFetch(
  url: string,
  init?: RequestInit,
): Promise<Response> {
  return fetch(url, init);
}
