import { proxyToApi } from "@/shared/server/proxy-api";

export async function POST(req: Request) {
  const body = await req.text();
  return proxyToApi("/v1/reports/query", { method: "POST", body });
}
