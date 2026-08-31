"use client";

import { useEffect, useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import type {
  KnowledgeDocumentItem,
  KnowledgeReindexResponse,
  KnowledgeSearchResponse,
  KnowledgeSearchResult,
  KnowledgeStats,
  KnowledgeUploadResponse,
} from "@/lib/types";

const UPLOAD_CATEGORIES = [
  { value: "uploads", label: "通用上传" },
  { value: "products", label: "产品资料" },
  { value: "amazon", label: "Amazon 规则" },
  { value: "tiktok", label: "TikTok 规则" },
  { value: "sop", label: "运营 SOP" },
  { value: "examples", label: "Listing 范例" },
] as const;

function formatBytes(size: number): string {
  if (size < 1024) {
    return `${size} B`;
  }
  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`;
  }
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

export default function KnowledgePage() {
  const [stats, setStats] = useState<KnowledgeStats | null>(null);
  const [documents, setDocuments] = useState<KnowledgeDocumentItem[]>([]);
  const [query, setQuery] = useState("Amazon title length");
  const [platform, setPlatform] = useState("amazon");
  const [uploadCategory, setUploadCategory] = useState("uploads");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [results, setResults] = useState<KnowledgeSearchResult[]>([]);
  const [reindexInfo, setReindexInfo] = useState<KnowledgeReindexResponse | null>(null);
  const [uploadInfo, setUploadInfo] = useState<KnowledgeUploadResponse | null>(null);
  const [loading, setLoading] = useState<"stats" | "docs" | "search" | "reindex" | "upload" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [docNotice, setDocNotice] = useState<string | null>(null);

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

  async function loadDocuments() {
    setLoading("docs");
    setDocNotice(null);
    try {
      const response = await fetch("/api/knowledge?view=documents");
      const payload = await response.json();
      if (!response.ok) {
        setDocuments([]);
        setDocNotice("文档列表暂不可用，请重启 API 后刷新。");
        return;
      }
      const data = payload.data as { items: KnowledgeDocumentItem[] };
      setDocuments(data.items);
      if (data.items.length === 0) {
        setDocNotice("暂无已入库文档，可上传文件或点「重建索引」。");
      }
    } catch {
      setDocuments([]);
      setDocNotice("文档列表加载失败，请确认 API 已更新并运行在 8000 端口。");
    } finally {
      setLoading(null);
    }
  }

  useEffect(() => {
    void loadStats();
    void loadDocuments();
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
      if (stats?.total_chunks === 0) {
        await loadStats();
      }
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
      await loadDocuments();
    } catch (err) {
      setError(err instanceof Error ? err.message : "重建索引失败");
    } finally {
      setLoading(null);
    }
  }

  async function handleUpload(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedFile) {
      setError("请选择文件");
      return;
    }

    setLoading("upload");
    setError(null);
    setUploadInfo(null);
    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("category", uploadCategory);

      const response = await fetch("/api/knowledge/upload", {
        method: "POST",
        body: formData,
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error ?? "上传失败");
      }

      const data = payload.data as KnowledgeUploadResponse;
      setUploadInfo(data);
      setReindexInfo(data.reindex);
      setSelectedFile(null);
      event.currentTarget.reset();
      await loadStats();
      await loadDocuments();
    } catch (err) {
      setError(err instanceof Error ? err.message : "上传失败");
    } finally {
      setLoading(null);
    }
  }

  return (
    <AppShell title="知识库" description="上传文档、自动入库、检索与重建索引">
      <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
        <section className="space-y-4">
          <div className="card">
            <p className="text-sm text-[var(--muted)]">索引块数</p>
            <p className="mt-2 text-3xl font-semibold">{stats?.total_chunks ?? "—"}</p>
            <button type="button" className="btn-secondary mt-4 w-full" onClick={() => void loadStats()}>
              刷新统计
            </button>
          </div>

          <form className="card space-y-3" onSubmit={handleUpload}>
            <h3 className="font-medium">上传文档</h3>
            <p className="text-sm text-[var(--muted)]">
              支持 .md / .json / .txt / .pdf / .docx，单文件 ≤ 10MB。上传后自动重建索引。
            </p>
            <div>
              <label className="mb-2 block text-sm font-medium" htmlFor="category">
                分类目录
              </label>
              <select
                id="category"
                className="input"
                value={uploadCategory}
                onChange={(event) => setUploadCategory(event.target.value)}
              >
                {UPLOAD_CATEGORIES.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-2 block text-sm font-medium" htmlFor="file">
                选择文件
              </label>
              <input
                id="file"
                type="file"
                className="input"
                accept=".md,.json,.txt,.pdf,.docx"
                onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
              />
            </div>
            <button type="submit" className="btn-primary w-full" disabled={loading === "upload"}>
              {loading === "upload" ? "上传中..." : "上传并入库"}
            </button>
            {uploadInfo ? (
              <p className="text-sm text-green-700 dark:text-green-400">
                已入库：{uploadInfo.source_file}（{uploadInfo.reindex.chunks} 块）
              </p>
            ) : null}
          </form>

          <div className="card space-y-3">
            <h3 className="font-medium">重建索引</h3>
            <p className="text-sm text-[var(--muted)]">从 knowledge/ 目录重新 ingest 全部文档。</p>
            <button
              type="button"
              className="btn-secondary w-full"
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

          <div className="card space-y-3">
            <div className="flex items-center justify-between gap-2">
              <h3 className="font-medium">已入库文档</h3>
              <button type="button" className="btn-secondary" onClick={() => void loadDocuments()}>
                刷新
              </button>
            </div>
            <div className="max-h-64 space-y-2 overflow-y-auto text-sm">
              {docNotice ? <p className="text-[var(--muted)]">{docNotice}</p> : null}
              {documents.length === 0 ? (
                !docNotice ? <p className="text-[var(--muted)]">暂无文档</p> : null
              ) : (
                documents.map((doc) => (
                  <div key={doc.source_file} className="rounded-lg border border-[var(--border)] px-3 py-2">
                    <p className="font-medium break-all">{doc.source_file}</p>
                    <p className="mt-1 text-xs text-[var(--muted)]">
                      {doc.extension} · {formatBytes(doc.size_bytes)}
                    </p>
                  </div>
                ))
              )}
            </div>
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
