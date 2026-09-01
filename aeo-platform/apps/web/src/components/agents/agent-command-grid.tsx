import type { AgentCatalogItem } from "@/lib/types";
import {
  agentDisplayName,
  categoryLabel,
  riskBadgeClass,
  statusLabel,
} from "@/lib/agent-display";

type AgentCommandGridProps = {
  agents: AgentCatalogItem[];
};

export function AgentCommandGrid({ agents }: AgentCommandGridProps) {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {agents.map((agent) => (
        <article key={agent.agent_id} className="card flex flex-col gap-3">
          <div className="flex items-start justify-between gap-2">
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-[var(--muted)]">
                {categoryLabel(agent.category)}
              </p>
              <h3 className="mt-1 text-lg font-semibold">{agentDisplayName(agent)}</h3>
              <p className="text-xs text-[var(--muted)]">{agent.agent_id}</p>
            </div>
            <span
              className={`rounded-full px-2 py-0.5 text-xs font-medium ${riskBadgeClass(agent.risk_level)}`}
            >
              {agent.risk_level}
            </span>
          </div>
          <p className="text-sm text-[var(--muted)]">{agent.description || "—"}</p>
          <div className="flex flex-wrap gap-2 text-xs">
            <span className="rounded-md bg-slate-100 px-2 py-1 dark:bg-slate-800">
              {statusLabel(agent.status)}
            </span>
            {agent.graph_node ? (
              <span className="rounded-md bg-slate-100 px-2 py-1 dark:bg-slate-800">
                节点: {agent.graph_node}
              </span>
            ) : null}
            <span className="rounded-md bg-slate-100 px-2 py-1 dark:bg-slate-800">
              能力 {agent.capabilities.length}
            </span>
          </div>
          {agent.capabilities.length > 0 ? (
            <ul className="mt-auto space-y-1 border-t border-[var(--border)] pt-3 text-xs text-[var(--muted)]">
              {agent.capabilities.slice(0, 3).map((capability) => (
                <li key={capability.name}>
                  <span className="font-medium text-[var(--foreground)]">{capability.name}</span>
                  {capability.description ? ` — ${capability.description}` : ""}
                </li>
              ))}
            </ul>
          ) : null}
        </article>
      ))}
    </div>
  );
}
