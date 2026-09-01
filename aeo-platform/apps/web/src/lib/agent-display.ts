import type { AgentCatalogItem } from "@/lib/types";

const CATEGORY_LABELS: Record<string, string> = {
  A01: "选品 A01",
  A02: "投放 A02",
  A03: "Listing A03",
  A04: "运维 A04",
  A05: "客服 A05",
  A06: "复盘 A06",
};

const STATUS_LABELS: Record<string, string> = {
  active: "运行中",
  planned: "规划中",
  deprecated: "已下线",
  disabled: "已禁用",
};

const RISK_STYLES: Record<string, string> = {
  L0: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200",
  L1: "bg-amber-100 text-amber-900 dark:bg-amber-900/40 dark:text-amber-200",
  L2: "bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-200",
};

export function categoryLabel(category: string): string {
  return CATEGORY_LABELS[category] ?? category;
}

export function statusLabel(status: string): string {
  return STATUS_LABELS[status] ?? status;
}

export function riskBadgeClass(riskLevel: string): string {
  return RISK_STYLES[riskLevel] ?? "bg-slate-100 text-slate-700";
}

export function agentDisplayName(agent: AgentCatalogItem): string {
  return agent.display_name || agent.agent_id;
}

export function sortAgents(agents: AgentCatalogItem[]): AgentCatalogItem[] {
  return [...agents].sort((left, right) => {
    if (left.category !== right.category) {
      return left.category.localeCompare(right.category);
    }
    return left.agent_id.localeCompare(right.agent_id);
  });
}
