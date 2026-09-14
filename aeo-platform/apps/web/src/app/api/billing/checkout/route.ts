import { NextRequest, NextResponse } from "next/server";
import { getBackendUrl } from "@/lib/backend-proxy";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const accessToken = request.cookies.get("access_token")?.value;

    const response = await fetch(`${getBackendUrl()}/api/v1/billing/checkout`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch {
    return NextResponse.json({ error: "请求失败" }, { status: 500 });
  }
}
