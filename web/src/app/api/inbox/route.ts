import { proxyToApi } from "@/shared/server/proxy-api";

export async function GET(req: Request) {
  const url = new URL(req.url);
  return proxyToApi(`/v1/inbox${url.search}`, { method: "GET" });
}

export async function POST(req: Request) {
  const body = await req.text();
  return proxyToApi("/v1/inbox", { method: "POST", body });
}
