import { useEffect, useState } from "react";

import type { Task } from "@/lib/types";

export type AgentTraceEvent = {
  task_id: string;
  agent: string;
  status: string;
  timestamp?: string;
  detail?: Record<string, unknown>;
};

export type TaskUpdatedEvent = {
  task_id: string;
  status: string;
  error_message?: string | null;
  final_output?: Record<string, unknown> | null;
  generated?: Record<string, unknown> | null;
};

type UseTaskEventsOptions = {
  onTaskUpdated?: (event: TaskUpdatedEvent) => void;
};

const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_DELAY_MS = 3000;

export function useTaskEvents(
  taskId: string | undefined,
  options: UseTaskEventsOptions = {},
): { events: AgentTraceEvent[]; connected: boolean; error: string | null } {
  const [events, setEvents] = useState<AgentTraceEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const onTaskUpdated = options.onTaskUpdated;

  useEffect(() => {
    if (!taskId) {
      return undefined;
    }

    let source: EventSource | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let reconnectAttempts = 0;
    let closed = false;

    const connect = () => {
      source = new EventSource(`/api/tasks/${taskId}/events`);
      source.onopen = () => {
        setConnected(true);
        setError(null);
        reconnectAttempts = 0;
      };

      source.addEventListener("agent.step", (message) => {
        try {
          const payload = JSON.parse(message.data) as AgentTraceEvent;
          setEvents((current) => {
            const key = `${payload.agent}-${payload.timestamp}-${payload.status}`;
            const exists = current.some(
              (item) => `${item.agent}-${item.timestamp}-${item.status}` === key,
            );
            if (exists) return current;
            return [...current, payload];
          });
        } catch {
          setError("Trace 事件解析失败");
        }
      });

      source.addEventListener("task.updated", (message) => {
        try {
          const payload = JSON.parse(message.data) as TaskUpdatedEvent;
          onTaskUpdated?.(payload);
        } catch {
          setError("任务状态事件解析失败");
        }
      });

      source.addEventListener("error", (message) => {
        if (message instanceof MessageEvent && message.data) {
          try {
            const payload = JSON.parse(message.data) as { message?: string };
            setError(payload.message ?? "SSE 连接错误");
          } catch {
            setError("SSE 连接错误");
          }
        }
      });

      source.onerror = () => {
        setConnected(false);
        source?.close();
        if (closed || reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
          setError((current) => current ?? "SSE 连接已断开");
          return;
        }
        reconnectAttempts += 1;
        reconnectTimer = setTimeout(connect, RECONNECT_DELAY_MS);
      };
    };

    connect();

    return () => {
      closed = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      source?.close();
    };
  }, [taskId, onTaskUpdated]);

  return { events, connected, error };
}

export function mergeTaskFromEvent(task: Task, event: TaskUpdatedEvent): Task {
  return {
    ...task,
    status: event.status ?? task.status,
    error_message: event.error_message ?? task.error_message,
    final_output:
      event.final_output !== undefined && event.final_output !== null
        ? event.final_output
        : task.final_output,
  };
}
