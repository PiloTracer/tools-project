import { proxyToApi } from "@/shared/server/proxy-api";

export async function GET(req: Request) {
  const url = new URL(req.url);
  return proxyToApi(`/v1/me/refs/search${url.search}`, { method: "GET" });
}
