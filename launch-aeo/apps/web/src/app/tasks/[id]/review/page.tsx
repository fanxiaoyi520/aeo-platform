"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { formatPlatform, formatTaskStatus } from "@/lib/task-status";
import {
  emptyListingDraft,
  listingFromGenerated,
  listingToPayload,
  type ListingDraft,
} from "@/lib/listing-draft";
import type { Task } from "@/lib/types";

function competitorAsins(productInfo: Record<string, unknown>): string[] {
  const raw = productInfo.competitor_asins;
  if (!Array.isArray(raw)) return [];
  return raw.map((item) => String(item)).filter(Boolean);
}

export default function TaskReviewPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const taskId = params.id;

  const [task, setTask] = useState<Task | null>(null);
  const [draft, setDraft] = useState<ListingDraft>(emptyListingDraft());
  const [feedback, setFeedback] = useState("");
  const [showReject, setShowReject] = useState(false);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState<"approve" | "reject" | null>(null);
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
        const data = payload.data as Task;
        setTask(data);
        const source =
          data.generated ??
          (data.final_output && typeof data.final_output === "object" ? data.final_output : null);
        setDraft(listingFromGenerated(source));
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

  async function handleApprove() {
    setSubmitting("approve");
    setError(null);
    try {
      const response = await fetch(`/api/tasks/${taskId}/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ listing: listingToPayload(draft) }),
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error ?? "批准失败");
      }
      router.push(`/tasks/${taskId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "批准失败");
    } finally {
      setSubmitting(null);
    }
  }

  async function handleReject() {
    if (!feedback.trim()) {
      setError("请填写驳回备注");
      return;
    }
    setSubmitting("reject");
    setError(null);
    try {
      const response = await fetch(`/api/tasks/${taskId}/reject`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ feedback: feedback.trim() }),
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error ?? "驳回失败");
      }
      router.push(`/tasks/${taskId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "驳回失败");
    } finally {
      setSubmitting(null);
    }
  }

  const status = task ? formatTaskStatus(task.status) : null;
  const asins = task ? competitorAsins(task.product_info) : [];
  const canReview = task?.status === "waiting_hitl";

  return (
    <AppShell title="人工审核" description="审核 AI 生成的 Listing 草稿并批准或驳回">
      <div className="mb-6 flex flex-wrap items-center gap-3">
        <Link href={`/tasks/${taskId}`} className="text-sm text-brand-600 hover:underline">
          ← 返回任务详情
        </Link>
      </div>

      {loading ? (
        <div className="card text-sm text-[var(--muted)]">加载中...</div>
      ) : error && !task ? (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
          {error}
        </div>
      ) : task ? (
        <div className="space-y-4">
          <div className="card flex flex-wrap items-center gap-3">
            <h3 className="text-lg font-semibold">{task.sku}</h3>
            {status ? (
              <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${status.className}`}>
                {status.label}
              </span>
            ) : null}
            <span className="text-sm text-[var(--muted)]">
              {formatPlatform(task.platform)} · {task.market}
            </span>
          </div>

          {!canReview ? (
            <div className="card text-sm text-[var(--muted)]">
              当前任务不在待审核状态，无法执行 HITL 操作。
            </div>
          ) : (
            <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
              <div className="card space-y-4">
                <h4 className="font-medium">AI 生成内容（可编辑）</h4>
                <div>
                  <label className="mb-2 block text-sm font-medium" htmlFor="title">
                    标题
                  </label>
                  <input
                    id="title"
                    className="input"
                    value={draft.title}
                    onChange={(event) => setDraft({ ...draft, title: event.target.value })}
                  />
                </div>
                {draft.bullets.map((bullet, index) => (
                  <div key={`bullet-${index}`}>
                    <label className="mb-2 block text-sm font-medium" htmlFor={`bullet-${index}`}>
                      Bullet {index + 1}
                    </label>
                    <textarea
                      id={`bullet-${index}`}
                      className="input min-h-[72px]"
                      value={bullet}
                      onChange={(event) => {
                        const bullets = [...draft.bullets];
                        bullets[index] = event.target.value;
                        setDraft({ ...draft, bullets });
                      }}
                    />
                  </div>
                ))}
                <div>
                  <label className="mb-2 block text-sm font-medium" htmlFor="search_terms">
                    Search Terms
                  </label>
                  <input
                    id="search_terms"
                    className="input"
                    value={draft.search_terms}
                    onChange={(event) => setDraft({ ...draft, search_terms: event.target.value })}
                  />
                </div>
                <div>
                  <label className="mb-2 block text-sm font-medium" htmlFor="description">
                    描述
                  </label>
                  <textarea
                    id="description"
                    className="input min-h-[120px]"
                    value={draft.description}
                    onChange={(event) => setDraft({ ...draft, description: event.target.value })}
                  />
                </div>
              </div>

              <div className="space-y-4">
                <div className="card space-y-3">
                  <h4 className="font-medium">参考信息</h4>
                  <div>
                    <p className="text-xs text-[var(--muted)]">竞品 ASIN</p>
                    {asins.length > 0 ? (
                      <ul className="mt-1 list-disc pl-5 text-sm">
                        {asins.map((asin) => (
                          <li key={asin}>{asin}</li>
                        ))}
                      </ul>
                    ) : (
                      <p className="mt-1 text-sm text-[var(--muted)]">未提供竞品 ASIN</p>
                    )}
                  </div>
                  <div>
                    <p className="text-xs text-[var(--muted)]">Trace 事件数</p>
                    <p className="mt-1 text-sm">{task.trace.length}</p>
                  </div>
                </div>

                <div className="card space-y-3">
                  <button
                    type="button"
                    className="btn-primary w-full"
                    disabled={submitting !== null}
                    onClick={() => void handleApprove()}
                  >
                    {submitting === "approve" ? "提交中..." : "批准发布"}
                  </button>
                  <button
                    type="button"
                    className="btn-secondary w-full"
                    disabled={submitting !== null}
                    onClick={() => setShowReject((value) => !value)}
                  >
                    驳回并备注
                  </button>
                  {showReject ? (
                    <div className="space-y-2">
                      <textarea
                        className="input min-h-[96px]"
                        placeholder="说明需要修改的内容，例如：标题过长、禁用词..."
                        value={feedback}
                        onChange={(event) => setFeedback(event.target.value)}
                      />
                      <button
                        type="button"
                        className="btn-secondary w-full border-red-300 text-red-700 dark:border-red-800 dark:text-red-300"
                        disabled={submitting !== null}
                        onClick={() => void handleReject()}
                      >
                        {submitting === "reject" ? "提交中..." : "确认驳回"}
                      </button>
                    </div>
                  ) : null}
                </div>
              </div>
            </div>
          )}

          {error ? (
            <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
              {error}
            </div>
          ) : null}
        </div>
      ) : null}
    </AppShell>
  );
}
