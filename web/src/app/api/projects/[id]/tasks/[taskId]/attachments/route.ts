import { cookies } from "next/headers";
import { NextResponse } from "next/server";

const SESSION = process.env.SESSION_COOKIE_NAME || "prj_auth";

export async function POST(
  req: Request,
  { params }: { params: Promise<{ id: string; taskId: string }> },
) {
  const jar = await cookies();
  const token = jar.get(SESSION)?.value;
  if (!token) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }
  const { id: projectId, taskId } = await params;
  const base =
    process.env.API_INTERNAL_URL?.replace(/\/+$/, "") || "http://api:8300";
  const fd = await req.formData();
  const r = await fetch(`${base}/v1/projects/${projectId}/tasks/${taskId}/attachments`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: fd,
  });
  return new NextResponse(await r.text(), { status: r.status });
}
