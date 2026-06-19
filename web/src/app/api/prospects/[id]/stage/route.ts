import { proxyToApi } from "@/shared/server/proxy-api";

export async function PATCH(
  req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const body = await req.text();
  return proxyToApi(`/v1/prospects/${id}/stage`, { method: "PATCH", body });
}
