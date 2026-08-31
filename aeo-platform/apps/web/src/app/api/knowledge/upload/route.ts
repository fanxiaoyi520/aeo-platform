import { NextResponse } from "next/server";

import { backendUpload } from "@/lib/backend";
import type { KnowledgeUploadResponse } from "@/lib/types";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  try {
    const incoming = await request.formData();
    const file = incoming.get("file");
    if (!(file instanceof File)) {
      return NextResponse.json({ error: "请选择要上传的文件" }, { status: 400 });
    }

    const category = incoming.get("category");
    const formData = new FormData();
    formData.append("file", file);
    formData.append("category", typeof category === "string" && category ? category : "uploads");

    const data = await backendUpload<KnowledgeUploadResponse>("/api/v1/knowledge/upload", formData);
    return NextResponse.json({ data });
  } catch (error) {
    const message = error instanceof Error ? error.message : "上传失败";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
