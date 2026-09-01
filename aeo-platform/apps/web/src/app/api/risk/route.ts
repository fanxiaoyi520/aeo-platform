import { NextResponse } from "next/server";

const API_BASE = process.env.API_BASE_URL ?? "http://127.0.0.1:8000";
const API_KEY = process.env.API_KEY ?? "dev-api-key-change-in-production";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const action = searchParams.get("action");
  const limit = searchParams.get("limit") ?? "100";

  const url = new URL("/api/v1/risk/audit", API_BASE);
  if (action) {
    url.searchParams.set("action", action);
  }
  url.searchParams.set("limit", limit);

  try {
    const response = await fetch(url.toString(), {
      headers: { Authorization: `Bearer ${API_KEY}` },
    });
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch {
    return NextResponse.json(
      { code: -1, message: "Failed to fetch risk audit logs", data: null },
      { status: 500 }
    );
  }
}

export async function POST(request: Request) {
  const body = await request.json();

  try {
    const response = await fetch(`${API_BASE}/api/v1/risk/evaluate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${API_KEY}`,
      },
      body: JSON.stringify(body),
    });
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch {
    return NextResponse.json(
      { code: -1, message: "Failed to evaluate risk", data: null },
      { status: 500 }
    );
  }
}
