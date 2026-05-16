import { proxyToApi } from "@/shared/server/proxy-api";

export async function POST(req: Request) {
  const body = await req.text();
  return proxyToApi("/v1/me/watch", { method: "POST", body });
}

export async function DELETE(req: Request) {
  const body = await req.text();
  return proxyToApi("/v1/me/watch", { method: "DELETE", body });
}
