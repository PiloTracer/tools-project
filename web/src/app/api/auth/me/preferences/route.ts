import { proxyToApi } from "@/shared/server/proxy-api";

export async function PATCH(req: Request) {
  const body = await req.text();
  return proxyToApi("/v1/auth/me/preferences", { method: "PATCH", body });
}
