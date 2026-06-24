import { proxyToApi } from "@/shared/server/proxy-api";

export async function POST(
  _req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  return proxyToApi(`/v1/prospects/${id}/promote`, { method: "POST" });
}
