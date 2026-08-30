"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { formatPlatform, formatTaskStatus } from "@/lib/task-status";
import type { Task, TaskList } from "@/lib/types";

const PAGE_SIZE = 20;

function formatDate(value: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("zh-CN", { hour12: false });
}

export default function TasksPageClient() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const page = Math.max(1, Number(searchParams.get("page") ?? "1") || 1);

  const [tasks, setTasks] = useState<Task[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadTasks = useCallback(async (targetPage: number) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/tasks?page=${targetPage}&page_size=${PAGE_SIZE}`);
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error ?? "加载任务列表失败");
      }
      const data = payload.data as TaskList;
      setTasks(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载任务列表失败");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadTasks(page);
  }, [loadTasks, page]);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  function goToPage(nextPage: number) {
    const clamped = Math.min(Math.max(1, nextPage), totalPages);
    router.push(clamped === 1 ? "/tasks" : `/tasks?page=${clamped}`);
  }

  return (
    <AppShell title="任务" description="Listing 优化任务列表与创建入口">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-[var(--muted)]">共 {total} 条任务</p>
        <Link href="/tasks/new" className="btn-primary">
          新建任务
        </Link>
      </div>

      {error ? (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
          {error}
        </div>
      ) : null}

      <div className="card overflow-x-auto p-0">
        <table className="min-w-full text-left text-sm">
          <thead
            className="border-b text-xs uppercase tracking-wide text-[var(--muted)]"
            style={{ borderColor: "var(--border)" }}
          >
            <tr>
              <th className="px-4 py-3 font-medium">SKU</th>
              <th className="px-4 py-3 font-medium">平台</th>
              <th className="px-4 py-3 font-medium">市场</th>
              <th className="px-4 py-3 font-medium">状态</th>
              <th className="px-4 py-3 font-medium">创建时间</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-[var(--muted)]">
                  加载中...
                </td>
              </tr>
            ) : tasks.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-[var(--muted)]">
                  暂无任务。
                  <Link href="/tasks/new" className="ml-2 text-brand-600 hover:underline">
                    创建第一个任务
                  </Link>
                </td>
              </tr>
            ) : (
              tasks.map((task) => {
                const status = formatTaskStatus(task.status);
                return (
                  <tr
                    key={task.id}
                    className="cursor-pointer border-b transition hover:bg-slate-50 dark:hover:bg-slate-900/40"
                    style={{ borderColor: "var(--border)" }}
                    onClick={() => router.push(`/tasks/${task.id}`)}
                  >
                    <td className="px-4 py-3 font-medium">{task.sku}</td>
                    <td className="px-4 py-3">{formatPlatform(task.platform)}</td>
                    <td className="px-4 py-3">{task.market}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`rounded-full px-2.5 py-1 text-xs font-medium ${status.className}`}
                      >
                        {status.label}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-[var(--muted)]">{formatDate(task.created_at)}</td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {totalPages > 1 ? (
        <div className="mt-4 flex items-center justify-between gap-3">
          <p className="text-sm text-[var(--muted)]">
            第 {page} / {totalPages} 页
          </p>
          <div className="flex gap-2">
            <button
              type="button"
              className="btn-secondary"
              disabled={page <= 1 || loading}
              onClick={() => goToPage(page - 1)}
            >
              上一页
            </button>
            <button
              type="button"
              className="btn-secondary"
              disabled={page >= totalPages || loading}
              onClick={() => goToPage(page + 1)}
            >
              下一页
            </button>
          </div>
        </div>
      ) : null}
    </AppShell>
  );
}
