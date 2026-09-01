"use client";

import { useCallback, useEffect, useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import type {
  RiskAuditItem,
  RiskDecision,
  RiskEffect,
  RiskLevel,
  RiskRule,
} from "@/lib/types";

const DEFAULT_RULES: RiskRule[] = [
  { rule_id: "l0_research_read", action: "research.read", risk_level: "L0", effect: "allow", description: "只读调研自动允许", priority: 10 },
  { rule_id: "l0_listing_generate", action: "listing.generate", risk_level: "L0", effect: "allow", description: "草稿生成自动允许", priority: 20 },
  { rule_id: "l1_listing_publish", action: "listing.publish", risk_level: "L1", effect: "require_hitl", description: "发布需人工审批", priority: 30 },
  { rule_id: "l1_price_update", action: "price.update", risk_level: "L1", effect: "require_hitl", description: "改价需人工审批", priority: 40 },
  { rule_id: "l1_ads_bid", action: "ads.bid_change", risk_level: "L1", effect: "require_hitl", description: "广告出价需人工审批", priority: 50 },
  { rule_id: "l1_ads_budget", action: "ads.budget_change", risk_level: "L1", effect: "require_hitl", description: "广告预算需人工审批", priority: 60 },
  { rule_id: "l2_new_account", action: "account.open", risk_level: "L2", effect: "deny", description: "新开户仅建议", priority: 70 },
  { rule_id: "l2_high_budget", action: "ads.budget_change", risk_level: "L2", effect: "deny", description: "预算 > 10000 拒绝", priority: 5 },
];

const RISK_ACTIONS = [
  { value: "research.read", label: "调研读取" },
  { value: "listing.generate", label: "生成 Listing" },
  { value: "listing.publish", label: "发布 Listing" },
  { value: "price.update", label: "修改价格" },
  { value: "ads.bid_change", label: "修改广告出价" },
  { value: "ads.budget_change", label: "修改广告预算" },
  { value: "account.open", label: "开设新账户" },
];

function getLevelColor(level: RiskLevel): string {
  switch (level) {
    case "L0":
      return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200";
    case "L1":
      return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200";
    case "L2":
      return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200";
  }
}

function getEffectColor(effect: RiskEffect): string {
  switch (effect) {
    case "allow":
      return "text-green-600 dark:text-green-400";
    case "require_hitl":
      return "text-yellow-600 dark:text-yellow-400";
    case "deny":
      return "text-red-600 dark:text-red-400";
  }
}

function getEffectLabel(effect: RiskEffect): string {
  switch (effect) {
    case "allow":
      return "自动允许";
    case "require_hitl":
      return "需人审";
    case "deny":
      return "拒绝";
  }
}

export default function RiskPage() {
  const [auditLogs, setAuditLogs] = useState<RiskAuditItem[]>([]);
  const [loading, setLoading] = useState<"audit" | "evaluate" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filterAction, setFilterAction] = useState("");

  const [testAction, setTestAction] = useState("listing.publish");
  const [testContext, setTestContext] = useState('{"sku": "DEMO-001"}');
  const [testResult, setTestResult] = useState<RiskDecision | null>(null);

  const loadAuditLogs = useCallback(async () => {
    setLoading("audit");
    setError(null);
    try {
      const url = filterAction ? `/api/risk?action=${filterAction}` : "/api/risk";
      const response = await fetch(url);
      const payload = await response.json();
      if (payload.code === 0) {
        setAuditLogs(payload.data.items);
      } else {
        setError(payload.message || "加载失败");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载失败");
    } finally {
      setLoading(null);
    }
  }, [filterAction]);

  useEffect(() => {
    void loadAuditLogs();
  }, [loadAuditLogs]);

  async function handleEvaluate(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading("evaluate");
    setError(null);
    setTestResult(null);

    let context: Record<string, unknown> = {};
    try {
      context = testContext ? JSON.parse(testContext) : {};
    } catch {
      setError("Context 格式错误，请输入有效的 JSON");
      setLoading(null);
      return;
    }

    try {
      const response = await fetch("/api/risk", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: testAction, context }),
      });
      const payload = await response.json();
      if (payload.code === 0) {
        setTestResult(payload.data);
        await loadAuditLogs();
      } else {
        setError(payload.message || "评估失败");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "评估失败");
    } finally {
      setLoading(null);
    }
  }

  const rulesByLevel = {
    L0: DEFAULT_RULES.filter((r) => r.risk_level === "L0"),
    L1: DEFAULT_RULES.filter((r) => r.risk_level === "L1"),
    L2: DEFAULT_RULES.filter((r) => r.risk_level === "L2"),
  };

  return (
    <AppShell title="风控中心" description="L0/L1/L2 风控规则展示、决策历史与测试">
      <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
        <section className="space-y-6">
          <div className="card">
            <h3 className="mb-4 font-medium">风控规则</h3>
            <div className="space-y-4">
              {(["L0", "L1", "L2"] as RiskLevel[]).map((level) => (
                <div key={level}>
                  <div className="mb-2 flex items-center gap-2">
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${getLevelColor(level)}`}>
                      {level}
                    </span>
                    <span className="text-sm text-[var(--muted)]">
                      {level === "L0" ? "自动执行" : level === "L1" ? "需人审" : "仅建议"}
                    </span>
                  </div>
                  <div className="space-y-1">
                    {rulesByLevel[level].map((rule) => (
                      <div
                        key={rule.rule_id}
                        className="flex items-center justify-between rounded-lg border border-[var(--border)] px-3 py-2 text-sm"
                      >
                        <div>
                          <span className="font-mono text-xs text-[var(--muted)]">{rule.action}</span>
                          <p className="mt-0.5 text-[var(--muted)]">{rule.description}</p>
                        </div>
                        <span className={`text-xs font-medium ${getEffectColor(rule.effect)}`}>
                          {getEffectLabel(rule.effect)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="card">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="font-medium">决策历史</h3>
              <div className="flex gap-2">
                <select
                  className="input text-sm"
                  value={filterAction}
                  onChange={(e) => setFilterAction(e.target.value)}
                >
                  <option value="">全部操作</option>
                  {RISK_ACTIONS.map((a) => (
                    <option key={a.value} value={a.value}>{a.label}</option>
                  ))}
                </select>
                <button
                  type="button"
                  className="btn-secondary text-sm"
                  onClick={() => void loadAuditLogs()}
                >
                  刷新
                </button>
              </div>
            </div>
            {loading === "audit" ? (
              <p className="text-sm text-[var(--muted)]">加载中...</p>
            ) : auditLogs.length === 0 ? (
              <p className="text-sm text-[var(--muted)]">暂无决策记录</p>
            ) : (
              <div className="max-h-80 space-y-2 overflow-y-auto">
                {auditLogs.map((log) => (
                  <div
                    key={log.id}
                    className="rounded-lg border border-[var(--border)] px-3 py-2 text-sm"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs">{log.detail?.action}</span>
                      <div className="flex items-center gap-2">
                        {log.detail && (
                          <span className={`rounded-full px-2 py-0.5 text-xs ${getLevelColor(log.detail.risk_level)}`}>
                            {log.detail.risk_level}
                          </span>
                        )}
                        <span className={`text-xs ${log.detail && getEffectColor(log.detail.effect)}`}>
                          {log.detail && getEffectLabel(log.detail.effect)}
                        </span>
                      </div>
                    </div>
                    <div className="mt-1 flex items-center justify-between text-xs text-[var(--muted)]">
                      <span>{log.actor}</span>
                      <span>{new Date(log.created_at).toLocaleString()}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>

        <section className="space-y-4">
          <form className="card space-y-4" onSubmit={handleEvaluate}>
            <h3 className="font-medium">风控测试</h3>
            <div>
              <label className="mb-2 block text-sm font-medium" htmlFor="action">
                操作类型
              </label>
              <select
                id="action"
                className="input"
                value={testAction}
                onChange={(e) => setTestAction(e.target.value)}
              >
                {RISK_ACTIONS.map((a) => (
                  <option key={a.value} value={a.value}>{a.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-2 block text-sm font-medium" htmlFor="context">
                Context (JSON)
              </label>
              <textarea
                id="context"
                className="input h-24 font-mono text-sm"
                value={testContext}
                onChange={(e) => setTestContext(e.target.value)}
                placeholder='{"sku": "DEMO-001"}'
              />
            </div>
            <button type="submit" className="btn-primary w-full" disabled={loading === "evaluate"}>
              {loading === "evaluate" ? "评估中..." : "评估"}
            </button>
            {testResult && (
              <div className="rounded-lg border border-[var(--border)] p-3">
                <p className="text-xs text-[var(--muted)]">决策结果</p>
                <div className="mt-2 space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span>允许</span>
                    <span className={testResult.allowed ? "text-green-600" : "text-red-600"}>
                      {testResult.allowed ? "是" : "否"}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>效果</span>
                    <span className={getEffectColor(testResult.effect)}>
                      {getEffectLabel(testResult.effect)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>风险等级</span>
                    <span className={`rounded-full px-2 py-0.5 text-xs ${getLevelColor(testResult.risk_level)}`}>
                      {testResult.risk_level}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>规则</span>
                    <span className="font-mono text-xs">{testResult.rule_id}</span>
                  </div>
                  <p className="mt-2 text-xs text-[var(--muted)]">{testResult.message}</p>
                </div>
              </div>
            )}
          </form>

          {error && (
            <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
              {error}
            </div>
          )}
        </section>
      </div>
    </AppShell>
  );
}
