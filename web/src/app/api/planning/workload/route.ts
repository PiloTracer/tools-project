import { proxyToApi } from "@/shared/server/proxy-api";

export async function GET() {
  return proxyToApi("/v1/planning/workload", { method: "GET" });
}
