import { proxyFormDataToApi } from "@/shared/server/proxy-api";

export async function POST(
  req: Request,
  { params }: { params: Promise<{ id: string; taskId: string }> },
) {
  const { id, taskId } = await params;
  const formData = await req.formData();
  return proxyFormDataToApi(`/v1/projects/${id}/tasks/${taskId}/attachments`, formData);
}
