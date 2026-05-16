import { proxyToApi } from "@/shared/server/proxy-api";

export async function GET() {
  return proxyToApi("/v1/admin/users", { method: "GET" });
}

export async function POST(req: Request) {
  const body = await req.text();
  return proxyToApi("/v1/admin/users", { method: "POST", body });
}
