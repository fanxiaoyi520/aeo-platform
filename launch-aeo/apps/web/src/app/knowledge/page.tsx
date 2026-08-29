"use client";

import { useEffect, useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import type {
  KnowledgeReindexResponse,
  KnowledgeSearchResponse,
  KnowledgeSearchResult,
  KnowledgeStats,
} from "@/lib/types";

export default function KnowledgePage() {
  const [stats, setStats] = useState<KnowledgeStats | null>(null);
  const [query, setQuery] = useState("Amazon title length");
  const [platform, setPlatform] = useState("amazon");
  const [results, setResults] = useState<KnowledgeSearchResult[]>([]);
  const [reindexInfo, setReindexInfo] = useState<KnowledgeReindexResponse | null>(null);
  const [loading, setLoading] = useState<"stats" | "search" | "reindex" | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadStats() {
    setLoading("stats");
    setError(null);
    try {
      const response = await fetch("/api/knowledge");
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error ?? "加载统计失败");
      }
      setStats(payload.data as KnowledgeStats);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载统计失败");
    } finally {
      setLoading(null);
    }
  }

  useEffect(() => {
    void loadStats();
  }, []);

  async function handleSearch(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading("search");
    setError(null);
    try {
      const response = await fetch("/api/knowledge", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "search", query, platform }),
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error ?? "检索失败");
      }
      const data = payload.data as KnowledgeSearchResponse;
      setResults(data.results);
    } catch (err) {
      setError(err instanceof Error ? err.message : "检索失败");
    } finally {
      setLoading(null);
    }
  }

  async function handleReindex() {
    setLoading("reindex");
    setError(null);
    try {
      const response = await fetch("/api/knowledge", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "reindex" }),
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error ?? "重建索引失败");
      }
      const data = payload.data as KnowledgeReindexResponse;
      setReindexInfo(data);
      await loadStats();
    } catch (err) {
      setError(err instanceof Error ? err.message : "重建索引失败");
    } finally {
      setLoading(null);
    }
  }

  return (
    <AppShell title="知识库" description="文档索引、检索与重建（对接 /api/v1/knowledge）">
      <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
        <section className="space-y-4">
          <div className="card">
            <p className="text-sm text-[var(--muted)]">索引块数</p>
            <p className="mt-2 text-3xl font-semibold">{stats?.total_chunks ?? "—"}</p>
            <button type="button" className="btn-secondary mt-4 w-full" onClick={() => void loadStats()}>
              刷新统计
            </button>
          </div>

          <div className="card space-y-3">
            <h3 className="font-medium">重建索引</h3>
            <p className="text-sm text-[var(--muted)]">从 knowledge/ 目录重新 ingest 全部文档。</p>
            <button
              type="button"
              className="btn-primary w-full"
              disabled={loading === "reindex"}
              onClick={() => void handleReindex()}
            >
              {loading === "reindex" ? "重建中..." : "重建索引"}
            </button>
            {reindexInfo ? (
              <p className="text-sm text-green-700 dark:text-green-400">
                完成：{reindexInfo.documents} 文档 / {reindexInfo.chunks} 块
              </p>
            ) : null}
          </div>
        </section>

        <section className="space-y-4">
          <form className="card space-y-4" onSubmit={handleSearch}>
            <div>
              <label className="mb-2 block text-sm font-medium" htmlFor="query">
                检索问题
              </label>
              <input
                id="query"
                className="input"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="例如：Amazon 标题字数限制"
              />
            </div>
            <div>
              <label className="mb-2 block text-sm font-medium" htmlFor="platform">
                平台
              </label>
              <select
                id="platform"
                className="input"
                value={platform}
                onChange={(event) => setPlatform(event.target.value)}
              >
                <option value="amazon">Amazon</option>
                <option value="tiktok">TikTok</option>
                <option value="general">General</option>
              </select>
            </div>
            <button type="submit" className="btn-primary" disabled={loading === "search"}>
              {loading === "search" ? "检索中..." : "检索"}
            </button>
          </form>

          {error ? (
            <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
              {error}
            </div>
          ) : null}

          <div className="space-y-3">
            {results.map((item) => (
              <article key={`${item.doc_id}-${item.chunk_index}`} className="card">
                <div className="mb-2 flex flex-wrap items-center gap-2 text-xs text-[var(--muted)]">
                  <span className="rounded-full bg-slate-100 px-2 py-1 dark:bg-slate-800">{item.platform}</span>
                  <span className="rounded-full bg-slate-100 px-2 py-1 dark:bg-slate-800">{item.category}</span>
                  <span>score {item.score.toFixed(3)}</span>
                </div>
                <p className="text-sm leading-6">{item.content}</p>
                <p className="mt-3 text-xs text-[var(--muted)]">{item.source_file}</p>
              </article>
            ))}
            {results.length === 0 ? (
              <div className="card text-sm text-[var(--muted)]">输入问题后点击检索查看结果。</div>
            ) : null}
          </div>
        </section>
      </div>
    </AppShell>
  );
}
