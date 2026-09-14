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

type RouteContext = { params: { id: string } };

export async function PATCH(request: Request, { params }: RouteContext) {
  try {
    const token = getAccessToken();
    const body = (await request.json()) as { role: string };
    const data = await backendFetch<TenantMember>(
      `/api/v1/tenants/me/users/${encodeURIComponent(params.id)}`,
      { method: "PATCH", body, accessToken: token },
    );
    return NextResponse.json({ data });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed to update member";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

export async function DELETE(_request: Request, { params }: RouteContext) {
  try {
    const token = getAccessToken();
    const data = await backendFetch<{ ok: boolean }>(
      `/api/v1/tenants/me/users/${encodeURIComponent(params.id)}`,
      { method: "DELETE", accessToken: token },
    );
    return NextResponse.json({ data });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed to deactivate member";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
