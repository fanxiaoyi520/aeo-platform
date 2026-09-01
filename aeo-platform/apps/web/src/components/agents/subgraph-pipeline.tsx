import type { AgentCatalogItem, SubGraphSummary } from "@/lib/types";
import { agentDisplayName } from "@/lib/agent-display";

type SubgraphPipelineProps = {
  graph: SubGraphSummary;
  agentsById: Record<string, AgentCatalogItem>;
};

export function SubgraphPipeline({ graph, agentsById }: SubgraphPipelineProps) {
  return (
    <section className="card">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-2">
        <div>
          <h2 className="text-lg font-semibold">{graph.display_name}</h2>
          <p className="text-sm text-[var(--muted)]">{graph.description}</p>
        </div>
        <p className="text-sm text-[var(--muted)]">{graph.step_count} 步流水线</p>
      </div>
      <ol className="flex flex-col gap-3 md:flex-row md:flex-wrap md:items-stretch">
        {graph.agent_ids.map((agentId, index) => {
          const agent = agentsById[agentId];
          return (
            <li
              key={agentId}
              className="flex min-w-[10rem] flex-1 flex-col rounded-lg border border-[var(--border)] bg-slate-50 p-3 dark:bg-slate-900/40"
            >
              <span className="text-xs font-medium text-[var(--muted)]">Step {index + 1}</span>
              <span className="mt-1 font-medium">
                {agent ? agentDisplayName(agent) : agentId}
              </span>
              <span className="mt-1 text-xs text-[var(--muted)]">{agentId}</span>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
