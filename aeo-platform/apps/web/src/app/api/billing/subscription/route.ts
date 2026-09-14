import { NextRequest, NextResponse } from "next/server";
import { getBackendUrl } from "@/lib/backend-proxy";

export async function GET(request: NextRequest) {
  try {
    const accessToken = request.cookies.get("access_token")?.value;

    const response = await fetch(`${getBackendUrl()}/api/v1/billing/subscription`, {
      headers: {
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      },
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch {
    return NextResponse.json({ error: "请求失败" }, { status: 500 });
  }
}
