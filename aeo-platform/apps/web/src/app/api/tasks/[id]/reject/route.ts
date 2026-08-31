import { NextResponse } from "next/server";

import { backendFetch } from "@/lib/backend";
import type { Task } from "@/lib/types";

type RouteContext = {
  params: Promise<{ id: string }>;
};

export async function POST(request: Request, context: RouteContext) {
  const { id } = await context.params;

  try {
    const body = (await request.json()) as { feedback?: string };
    const data = await backendFetch<Task>(`/api/v1/tasks/${encodeURIComponent(id)}/reject`, {
      method: "POST",
      body: { feedback: body.feedback ?? "" },
    });
    return NextResponse.json({ data });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed to reject task";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
