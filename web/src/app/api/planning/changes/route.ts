import { proxyToApi } from "@/shared/server/proxy-api";

export async function GET(req: Request) {
  const qs = new URL(req.url).searchParams.toString();
  return proxyToApi(`/v1/planning/changes?${qs}`, { method: "GET" });
}
