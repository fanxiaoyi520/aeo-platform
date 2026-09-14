import { NextResponse } from "next/server";

import { getAccessToken } from "@/lib/auth";
import { backendFetch } from "@/lib/backend";

export const dynamic = "force-dynamic";

type TenantMember = {
  id: string;
  email: string;
  display_name: string | null;
  role: string;
  is_active: boolean;
  last_login_at: string | null;
  created_at: string;
};

type TenantMembersResponse = {
  items: TenantMember[];
  total: number;
};

export async function GET() {
  try {
    const token = getAccessToken();
    const data = await backendFetch<TenantMembersResponse>("/api/v1/tenants/me/users", {
      accessToken: token,
    });
    return NextResponse.json({ data });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed to load members";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const token = getAccessToken();
    const body = (await request.json()) as {
      email: string;
      display_name?: string;
      role?: string;
    };
    const data = await backendFetch<TenantMember>("/api/v1/tenants/me/users", {
      method: "POST",
      body,
      accessToken: token,
    });
    return NextResponse.json({ data });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed to invite member";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
