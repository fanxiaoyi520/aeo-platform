import { NextResponse } from "next/server";

import { backendFetch } from "@/lib/backend";
import type { CreateTaskPayload, Task, TaskList } from "@/lib/types";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const page = searchParams.get("page") ?? "1";
    const pageSize = searchParams.get("page_size") ?? "20";
    const data = await backendFetch<TaskList>(
      `/api/v1/tasks?page=${encodeURIComponent(page)}&page_size=${encodeURIComponent(pageSize)}`,
    );
    return NextResponse.json({ data });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed to load tasks";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as CreateTaskPayload;
    const data = await backendFetch<Task>("/api/v1/tasks", {
      method: "POST",
      body,
    });
    return NextResponse.json({ data });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed to create task";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
