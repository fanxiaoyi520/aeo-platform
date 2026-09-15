import { NextResponse } from "next/server";

import { backendFetch } from "@/lib/backend";
import type {
  RiskAuditListResponse,
  RiskDecision,
  RiskEvaluateRequest,
  RiskRuleSet,
} from "@/lib/types";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const [rules, audit] = await Promise.all([
      backendFetch<RiskRuleSet>("/api/v1/risk/rules"),
      backendFetch<RiskAuditListResponse>("/api/v1/risk/audit?limit=20"),
    ]);
    return NextResponse.json({ data: { rules, audit } });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Failed to load risk data";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as RiskEvaluateRequest;
    const data = await backendFetch<RiskDecision>("/api/v1/risk/evaluate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return NextResponse.json({ data });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Failed to evaluate risk";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
