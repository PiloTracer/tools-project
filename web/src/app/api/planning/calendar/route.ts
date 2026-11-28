import { proxyToApi } from "@/shared/server/proxy-api";

export async function GET(req: Request) {
  const qs = new URL(req.url).searchParams.toString();
  return proxyToApi(`/v1/planning/calendar${qs ? `?${qs}` : ""}`, { method: "GET" });
}
