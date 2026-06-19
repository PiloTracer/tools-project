import { proxyBinaryFromApi } from "@/shared/server/proxy-api";

export async function GET(req: Request) {
  const url = new URL(req.url);
  const qs = url.searchParams.toString();
  return proxyBinaryFromApi(`/v1/reports/pipeline${qs ? `?${qs}` : ""}`);
}
