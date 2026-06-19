import { proxyFormDataToApi } from "@/shared/server/proxy-api";

export async function POST(
  req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const fd = await req.formData();
  return proxyFormDataToApi(`/v1/projects/${id}/attachments`, fd);
}
