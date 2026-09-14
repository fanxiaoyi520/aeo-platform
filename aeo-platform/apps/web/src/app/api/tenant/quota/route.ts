import { NextResponse } from "next/server";

import { getAccessToken } from "@/lib/auth";
import { backendFetch } from "@/lib/backend";
import type { TenantQuota } from "@/lib/types";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const token = getAccessToken();
    const data = await backendFetch<TenantQuota>("/api/v1/tenants/me/quota", {
      accessToken: token,
    });
    return NextResponse.json({ data });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed to load quota";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
