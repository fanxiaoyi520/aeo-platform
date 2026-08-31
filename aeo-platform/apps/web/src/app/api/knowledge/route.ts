import { NextResponse } from "next/server";

import { backendFetch } from "@/lib/backend";
import type { KnowledgeDocumentsResponse, KnowledgeStats } from "@/lib/types";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    if (searchParams.get("view") === "documents") {
      try {
        const data = await backendFetch<KnowledgeDocumentsResponse>("/api/v1/knowledge/documents");
        return NextResponse.json({ data });
      } catch {
        // Older API builds lack GET /documents — keep the page usable.
        return NextResponse.json({ data: { items: [], total: 0 } });
      }
    }

    const data = await backendFetch<KnowledgeStats>("/api/v1/knowledge/stats");
    return NextResponse.json({ data });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed to load knowledge data";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as { action?: string; query?: string; platform?: string };
    if (body.action === "reindex") {
      const data = await backendFetch("/api/v1/knowledge/reindex", {
        method: "POST",
      });
      return NextResponse.json({ data });
    }

    if (body.action === "search") {
      const data = await backendFetch("/api/v1/knowledge/search", {
        method: "POST",
        body: {
          query: body.query,
          platform: body.platform || undefined,
          top_k: 5,
        },
      });
      return NextResponse.json({ data });
    }

    return NextResponse.json({ error: "Unknown action" }, { status: 400 });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Knowledge API request failed";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
