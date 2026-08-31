import { NextResponse } from "next/server";

const API_BASE_URL = process.env.API_BASE_URL ?? "http://127.0.0.1:8000";
const AUTH_API_KEY = process.env.AUTH_API_KEY ?? "dev-api-key-change-in-production";

type RouteContext = {
  params: Promise<{ id: string }>;
};

export async function GET(_request: Request, context: RouteContext) {
  const { id } = await context.params;

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/tasks/${encodeURIComponent(id)}/events`, {
      headers: {
        Authorization: `Bearer ${AUTH_API_KEY}`,
        Accept: "text/event-stream",
      },
      cache: "no-store",
    });

    if (!response.ok || !response.body) {
      const text = await response.text();
      return NextResponse.json(
        { error: text || `SSE upstream ${response.status}` },
        { status: response.status },
      );
    }

    return new Response(response.body, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache, no-transform",
        Connection: "keep-alive",
      },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed to open task event stream";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
