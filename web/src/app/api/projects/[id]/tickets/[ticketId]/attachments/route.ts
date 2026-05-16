import { proxyFormDataToApi } from "@/shared/server/proxy-api";

export async function POST(
  req: Request,
  { params }: { params: Promise<{ id: string; ticketId: string }> },
) {
  const { id, ticketId } = await params;
  const formData = await req.formData();
  return proxyFormDataToApi(`/v1/projects/${id}/tickets/${ticketId}/attachments`, formData);
}
