import { NextResponse } from "next/server";
import {
  AUTH_COOKIE,
  SESSION_COOKIE_OPTIONS,
  buildSessionCookie,
} from "@/lib/auth";

const API_BASE_URL = process.env.API_BASE_URL ?? "http://127.0.0.1:8000";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as {
      email: string;
      password: string;
      display_name?: string;
      tenant_name: string;
      tenant_slug: string;
    };

    const response = await fetch(`${API_BASE_URL}/api/v1/auth/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const data = (await response.json()) as {
      code: number;
      data: { access_token: string; refresh_token: string; user: unknown };
      message?: string;
    };

    if (!response.ok || data.code !== 0) {
      return NextResponse.json(
        { error: data.message || "注册失败" },
        { status: response.status || 400 }
      );
    }

    const sessionValue = buildSessionCookie(data.data.access_token, data.data.refresh_token);
    const res = NextResponse.json({ data: { user: data.data.user } });
    res.cookies.set(AUTH_COOKIE, sessionValue, SESSION_COOKIE_OPTIONS);
    return res;
  } catch {
    return NextResponse.json({ error: "注册失败" }, { status: 500 });
  }
}
