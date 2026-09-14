import { NextResponse } from "next/server";
import { decodeJwtPayload, getSessionToken, isTokenExpired } from "@/lib/auth";

const API_BASE_URL = process.env.API_BASE_URL ?? "http://127.0.0.1:8000";

export const dynamic = "force-dynamic";

export async function GET() {
  const token = getSessionToken();
  if (!token || isTokenExpired(token)) {
    return NextResponse.json({ error: "未登录" }, { status: 401 });
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
    });

    const data = (await response.json()) as {
      code: number;
      data: { user_id: string; tenant_id: string; role: string };
    };

    if (!response.ok || data.code !== 0) {
      return NextResponse.json({ error: "会话已过期" }, { status: 401 });
    }

    const payload = decodeJwtPayload(token);
    const email = (payload?.email as string) ?? "";

    return NextResponse.json({
      data: {
        user_id: data.data.user_id,
        tenant_id: data.data.tenant_id,
        role: data.data.role,
        email,
      },
    });
  } catch {
    return NextResponse.json({ error: "获取用户信息失败" }, { status: 500 });
  }
}
