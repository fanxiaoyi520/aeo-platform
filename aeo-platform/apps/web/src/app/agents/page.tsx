"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { AgentCommandGrid } from "@/components/agents/agent-command-grid";
import { SubgraphPipeline } from "@/components/agents/subgraph-pipeline";
import { AppShell } from "@/components/layout/app-shell";
import { sortAgents } from "@/lib/agent-display";
import type { AgentCommandConsole } from "@/lib/types";

export default function AgentsCommandConsolePage() {
  const [consoleData, setConsoleData] = useState<AgentCommandConsole | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch("/api/agents");
        const payload = await response.json();
        if (!response.ok) {
          throw new Error(payload.error ?? "加载指挥台失败");
        }
        setConsoleData(payload.data as AgentCommandConsole);
      } catch (err) {
        setError(err instanceof Error ? err.message : "加载指挥台失败");
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, []);

  const agents = useMemo(
    () => sortAgents(consoleData?.agents ?? []),
    [consoleData?.agents],
  );

  const agentsById = useMemo(() => {
    const map: Record<string, (typeof agents)[number]> = {};
    for (const agent of agents) {
      map[agent.agent_id] = agent;
    }
    return map;
  }, [agents]);

  const listingGraph = consoleData?.graphs.find((graph) => graph.graph_id === "listing");

  return (
    <AppShell
      title="Agent 指挥台"
      description="六类 Agent 注册状态与子图编排总览（MV4-07）"
    >
      {loading ? <p className="text-sm text-[var(--muted)]">加载中…</p> : null}
      {error ? <p className="text-sm text-rose-600">{error}</p> : null}

      {consoleData ? (
        <div className="space-y-6">
          <div className="grid gap-4 md:grid-cols-4">
            <div className="card">
              <p className="text-sm text-[var(--muted)]">注册 Agent</p>
              <p className="mt-2 text-3xl font-semibold">{consoleData.summary.total}</p>
            </div>
            <div className="card">
              <p className="text-sm text-[var(--muted)]">运行中</p>
              <p className="mt-2 text-3xl font-semibold text-emerald-600">
                {consoleData.summary.active}
              </p>
            </div>
            <div className="card">
              <p className="text-sm text-[var(--muted)]">规划中</p>
              <p className="mt-2 text-3xl font-semibold text-amber-600">
                {consoleData.summary.planned}
              </p>
            </div>
            <div className="card flex flex-col justify-between">
              <p className="text-sm text-[var(--muted)]">Listing 任务</p>
              <Link
                href="/tasks"
                className="mt-2 inline-flex text-sm font-medium text-brand-600 hover:underline"
              >
                前往任务列表 →
              </Link>
            </div>
          </div>

          {listingGraph ? (
            <SubgraphPipeline graph={listingGraph} agentsById={agentsById} />
          ) : null}

          <div>
            <h2 className="mb-3 text-lg font-semibold">Agent 目录</h2>
            <AgentCommandGrid agents={agents} />
          </div>
        </div>
      ) : null}
    </AppShell>
  );
}
