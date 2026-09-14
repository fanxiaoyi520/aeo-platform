import { NextResponse } from "next/server";

import { getAccessToken } from "@/lib/auth";
import { backendFetch } from "@/lib/backend";
import type { Task } from "@/lib/types";

type RouteContext = {
  params: Promise<{ id: string }>;
};

export async function GET(_request: Request, context: RouteContext) {
  try {
    const token = getAccessToken();
    const { id } = await context.params;
    const data = await backendFetch<Task>(`/api/v1/tasks/${encodeURIComponent(id)}`, {
      accessToken: token,
    });
    return NextResponse.json({ data });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed to load task";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
