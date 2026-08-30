"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { formatPlatform, formatTaskStatus } from "@/lib/task-status";
import type { Task } from "@/lib/types";

function formatDate(value: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("zh-CN", { hour12: false });
}

export default function TaskDetailPage() {
  const params = useParams<{ id: string }>();
  const taskId = params.id;

  const [task, setTask] = useState<Task | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadTask() {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`/api/tasks/${taskId}`);
        const payload = await response.json();
        if (!response.ok) {
          throw new Error(payload.error ?? "加载任务失败");
        }
        setTask(payload.data as Task);
      } catch (err) {
        setError(err instanceof Error ? err.message : "加载任务失败");
      } finally {
        setLoading(false);
      }
    }

    if (taskId) {
      void loadTask();
    }
  }, [taskId]);

  const status = task ? formatTaskStatus(task.status) : null;

  return (
    <AppShell title="任务详情" description="Agent Trace 与 HITL 审核将在后续版本接入">
      <div className="mb-6">
        <Link href="/tasks" className="text-sm text-brand-600 hover:underline">
          ← 返回任务列表
        </Link>
      </div>

      {loading ? (
        <div className="card text-sm text-[var(--muted)]">加载中...</div>
      ) : error ? (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
          {error}
        </div>
      ) : task ? (
        <div className="space-y-4">
          <div className="card space-y-4">
            <div className="flex flex-wrap items-center gap-3">
              <h3 className="text-lg font-semibold">{task.sku}</h3>
              {status ? (
                <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${status.className}`}>
                  {status.label}
                </span>
              ) : null}
            </div>
            <dl className="grid gap-3 text-sm sm:grid-cols-2">
              <div>
                <dt className="text-[var(--muted)]">任务 ID</dt>
                <dd className="mt-1 font-mono text-xs">{task.id}</dd>
              </div>
              <div>
                <dt className="text-[var(--muted)]">平台</dt>
                <dd className="mt-1">{formatPlatform(task.platform)}</dd>
              </div>
              <div>
                <dt className="text-[var(--muted)]">市场</dt>
                <dd className="mt-1">{task.market}</dd>
              </div>
              <div>
                <dt className="text-[var(--muted)]">创建时间</dt>
                <dd className="mt-1">{formatDate(task.created_at)}</dd>
              </div>
            </dl>
            {task.error_message ? (
              <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
                {task.error_message}
              </p>
            ) : null}
          </div>

          {task.status === "waiting_hitl" ? (
            <div className="card border-amber-200 bg-amber-50 text-sm text-amber-900 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-200">
              任务已暂停，等待人工审核。HITL 审核页（S5-03+）将在此提供批准/驳回操作。
            </div>
          ) : null}

          {task.final_output ? (
            <div className="card space-y-2">
              <h4 className="font-medium">生成结果（预览）</h4>
              <p className="text-sm">{String(task.final_output.title ?? "—")}</p>
            </div>
          ) : (
            <div className="card text-sm text-[var(--muted)]">
              Agent Trace 时间线与中间结果将在 S5-03 接入。
            </div>
          )}
        </div>
      ) : null}
    </AppShell>
  );
}
