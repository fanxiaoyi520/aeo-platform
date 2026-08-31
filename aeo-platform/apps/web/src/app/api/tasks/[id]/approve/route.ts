import { NextResponse } from "next/server";

import { backendFetch } from "@/lib/backend";
import type { Task } from "@/lib/types";

type RouteContext = {
  params: Promise<{ id: string }>;
};

export async function POST(request: Request, context: RouteContext) {
  const { id } = await context.params;
  let listing: Record<string, unknown> | undefined;
  try {
    const body = (await request.json()) as { listing?: Record<string, unknown> };
    listing = body.listing;
  } catch {
    listing = undefined;
  }

  try {
    const data = await backendFetch<Task>(`/api/v1/tasks/${encodeURIComponent(id)}/approve`, {
      method: "POST",
      body: listing ? { listing } : {},
    });
    return NextResponse.json({ data });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed to approve task";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
