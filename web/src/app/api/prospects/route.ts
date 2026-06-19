import { proxyToApi } from "@/shared/server/proxy-api";

export async function GET(req: Request) {
  const url = new URL(req.url);
  const qs = url.searchParams.toString();
  return proxyToApi(`/v1/prospects${qs ? `?${qs}` : ""}`, { method: "GET" });
}

export async function POST(req: Request) {
  const body = await req.text();
  return proxyToApi("/v1/prospects", { method: "POST", body });
}
