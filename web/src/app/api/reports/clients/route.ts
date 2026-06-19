import { proxyBinaryFromApi } from "@/shared/server/proxy-api";

export async function GET() {
  return proxyBinaryFromApi("/v1/reports/clients");
}
