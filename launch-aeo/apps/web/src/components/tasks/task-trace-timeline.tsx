import type { AgentTraceEvent } from "@/hooks/use-task-events";

function formatTime(timestamp: string | undefined): string {
  if (!timestamp) return "--:--:--";
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) return timestamp;
  return date.toLocaleTimeString("zh-CN", { hour12: false });
}

function traceStyle(agent: string, status: string): { dot: string; text: string } {
  if (agent === "human_review" || status === "waiting_hitl") {
    return {
      dot: "bg-amber-400",
      text: "text-amber-700 dark:text-amber-300",
    };
  }
  if (status === "failed") {
    return {
      dot: "bg-orange-400",
      text: "text-orange-700 dark:text-orange-300",
    };
  }
  if (status === "completed") {
    return {
      dot: "bg-green-500",
      text: "text-green-700 dark:text-green-300",
    };
  }
  if (status === "started") {
    return {
      dot: "bg-blue-400 animate-pulse",
      text: "text-blue-700 dark:text-blue-300",
    };
  }
  return {
    dot: "bg-slate-400",
    text: "text-[var(--muted)]",
  };
}

function traceLabel(agent: string, status: string): string {
  if (agent === "human_review" && status === "completed") {
    return "⏸ waiting for human review";
  }
  return `${agent} ${status}`;
}

type TaskTraceTimelineProps = {
  events: AgentTraceEvent[];
  connected: boolean;
};

export function TaskTraceTimeline({ events, connected }: TaskTraceTimelineProps) {
  return (
    <div className="card space-y-4">
      <div className="flex items-center justify-between gap-3">
        <h4 className="font-medium">Agent Trace</h4>
        <span className="text-xs text-[var(--muted)]">
          {connected ? "实时连接中" : "连接断开"}
        </span>
      </div>

      {events.length === 0 ? (
        <p className="text-sm text-[var(--muted)]">等待 Agent 事件...</p>
      ) : (
        <ol className="space-y-3">
          {events.map((event, index) => {
            const style = traceStyle(event.agent, event.status);
            return (
              <li key={`${event.agent}-${event.timestamp}-${index}`} className="flex gap-3 text-sm">
                <span className={`mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full ${style.dot}`} />
                <div className="min-w-0">
                  <p className="font-mono text-xs text-[var(--muted)]">
                    [{formatTime(event.timestamp)}]
                  </p>
                  <p className={style.text}>{traceLabel(event.agent, event.status)}</p>
                  {event.detail && Object.keys(event.detail).length > 0 ? (
                    <p className="mt-1 text-xs text-[var(--muted)]">
                      {JSON.stringify(event.detail)}
                    </p>
                  ) : null}
                </div>
              </li>
            );
          })}
        </ol>
      )}
    </div>
  );
}
