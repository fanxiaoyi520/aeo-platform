"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { formatPlatform, formatTaskStatus } from "@/lib/task-status";
import {
  buildExportFilename,
  copyText,
  downloadTextFile,
  formatListingForClipboard,
  listingFromFinalOutput,
  listingToCsv,
  listingToJson,
  listingVersionFromOutput,
  type ListingExportMeta,
} from "@/lib/listing-export";
import type { ListingDraft } from "@/lib/listing-draft";
import type { Task } from "@/lib/types";

type CopyKey = "title" | "search_terms" | "description" | "all" | `bullet-${number}`;

function FieldBlock({
  label,
  value,
  copyKey,
  copiedKey,
  onCopy,
}: {
  label: string;
  value: string;
  copyKey: CopyKey;
  copiedKey: CopyKey | null;
  onCopy: (key: CopyKey, text: string) => void;
}) {
  return (
    <div className="card space-y-2">
      <div className="flex items-center justify-between gap-3">
        <h4 className="font-medium">{label}</h4>
        <button
          type="button"
          className="btn-secondary px-3 py-1.5 text-xs"
          disabled={!value.trim()}
          onClick={() => onCopy(copyKey, value)}
        >
          {copiedKey === copyKey ? "已复制" : "复制"}
        </button>
      </div>
      <p className="whitespace-pre-wrap text-sm text-[var(--muted)]">{value || "—"}</p>
    </div>
  );
}

export default function TaskResultPage() {
  const params = useParams<{ id: string }>();
  const taskId = params.id;

  const [task, setTask] = useState<Task | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copiedKey, setCopiedKey] = useState<CopyKey | null>(null);

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

  const finalOutput = task?.final_output ?? null;
  const listing: ListingDraft = useMemo(
    () => listingFromFinalOutput(finalOutput),
    [finalOutput],
  );
  const hasListing =
    Boolean(finalOutput) &&
    (listing.title.trim().length > 0 ||
      listing.bullets.some((bullet) => bullet.trim().length > 0) ||
      listing.search_terms.trim().length > 0 ||
      listing.description.trim().length > 0);

  const exportMeta: ListingExportMeta | null = task
    ? {
        taskId: task.id,
        sku: task.sku,
        platform: task.platform,
        market: task.market,
        listingVersion: listingVersionFromOutput(finalOutput),
      }
    : null;

  async function handleCopy(key: CopyKey, text: string) {
    if (!text.trim()) return;
    try {
      await copyText(text);
      setCopiedKey(key);
      window.setTimeout(() => setCopiedKey(null), 2000);
    } catch {
      setError("复制失败，请手动选择文本复制");
    }
  }

  async function handleCopyAll() {
    await handleCopy("all", formatListingForClipboard(listing));
  }

  function handleDownloadJson() {
    if (!exportMeta) return;
    const filename = buildExportFilename(exportMeta, "json");
    downloadTextFile(filename, listingToJson(exportMeta, listing), "application/json;charset=utf-8");
  }

  function handleDownloadCsv() {
    if (!exportMeta) return;
    const filename = buildExportFilename(exportMeta, "csv");
    downloadTextFile(filename, listingToCsv(exportMeta, listing), "text/csv;charset=utf-8");
  }

  const status = task ? formatTaskStatus(task.status) : null;
  const canExport = task?.status === "completed" && hasListing;

  return (
    <AppShell title="Listing 结果" description="复制字段或导出 JSON/CSV，便于粘贴到 Seller Central">
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
            {exportMeta?.listingVersion ? (
              <span className="text-sm text-[var(--muted)]">
                版本 v{exportMeta.listingVersion}
              </span>
            ) : null}
          </div>

          {!canExport ? (
            <div className="card space-y-3 text-sm text-[var(--muted)]">
              <p>
                {task.status !== "completed"
                  ? "任务尚未完成，暂无最终 Listing 可导出。"
                  : "未找到可导出的 Listing 内容。"}
              </p>
              <Link href={`/tasks/${taskId}`} className="text-brand-600 hover:underline">
                返回任务详情
              </Link>
            </div>
          ) : (
            <>
              <div className="card flex flex-wrap gap-2">
                <button type="button" className="btn-primary" onClick={() => void handleCopyAll()}>
                  {copiedKey === "all" ? "已复制全部" : "复制全部"}
                </button>
                <button type="button" className="btn-secondary" onClick={handleDownloadJson}>
                  下载 JSON
                </button>
                <button type="button" className="btn-secondary" onClick={handleDownloadCsv}>
                  下载 CSV
                </button>
              </div>

              <FieldBlock
                label="标题"
                value={listing.title}
                copyKey="title"
                copiedKey={copiedKey}
                onCopy={(key, text) => void handleCopy(key, text)}
              />

              {listing.bullets.map((bullet, index) => (
                <FieldBlock
                  key={`bullet-${index}`}
                  label={`Bullet ${index + 1}`}
                  value={bullet}
                  copyKey={`bullet-${index}`}
                  copiedKey={copiedKey}
                  onCopy={(key, text) => void handleCopy(key, text)}
                />
              ))}

              <FieldBlock
                label="Search Terms"
                value={listing.search_terms}
                copyKey="search_terms"
                copiedKey={copiedKey}
                onCopy={(key, text) => void handleCopy(key, text)}
              />

              <FieldBlock
                label="描述"
                value={listing.description}
                copyKey="description"
                copiedKey={copiedKey}
                onCopy={(key, text) => void handleCopy(key, text)}
              />
            </>
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
