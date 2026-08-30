"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import type { CreateTaskPayload, Task, TaskPlatform } from "@/lib/types";

function parseListInput(value: string): string[] {
  return value
    .split(/[\n,]+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

export default function NewTaskPage() {
  const router = useRouter();
  const [sku, setSku] = useState("");
  const [platform, setPlatform] = useState<TaskPlatform>("amazon");
  const [market, setMarket] = useState("US");
  const [competitors, setCompetitors] = useState("");
  const [keywords, setKeywords] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);

    const competitorAsins = parseListInput(competitors);
    const keywordList = parseListInput(keywords);
    const payload: CreateTaskPayload = {
      sku: sku.trim(),
      platform,
      market: market.trim() || "US",
      product_info: {},
    };
    if (competitorAsins.length > 0) {
      payload.product_info!.competitor_asins = competitorAsins;
    }
    if (keywordList.length > 0) {
      payload.product_info!.keywords = keywordList;
    }

    try {
      const response = await fetch("/api/tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const body = await response.json();
      if (!response.ok) {
        throw new Error(body.error ?? "创建任务失败");
      }
      const task = body.data as Task;
      router.push(`/tasks/${task.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "创建任务失败");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppShell title="新建任务" description="提交 SKU 与平台信息，启动 Agent 编排流程">
      <form className="card mx-auto max-w-2xl space-y-5" onSubmit={handleSubmit}>
        <div>
          <label className="mb-2 block text-sm font-medium" htmlFor="sku">
            SKU <span className="text-red-500">*</span>
          </label>
          <input
            id="sku"
            className="input"
            value={sku}
            onChange={(event) => setSku(event.target.value)}
            placeholder="例如：X431"
            required
            maxLength={128}
          />
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-2 block text-sm font-medium" htmlFor="platform">
              平台 <span className="text-red-500">*</span>
            </label>
            <select
              id="platform"
              className="input"
              value={platform}
              onChange={(event) => setPlatform(event.target.value as TaskPlatform)}
            >
              <option value="amazon">Amazon</option>
              <option value="tiktok">TikTok</option>
            </select>
          </div>
          <div>
            <label className="mb-2 block text-sm font-medium" htmlFor="market">
              市场
            </label>
            <input
              id="market"
              className="input"
              value={market}
              onChange={(event) => setMarket(event.target.value)}
              placeholder="US"
              maxLength={16}
            />
          </div>
        </div>

        <div>
          <label className="mb-2 block text-sm font-medium" htmlFor="competitors">
            竞品 ASIN（可选）
          </label>
          <textarea
            id="competitors"
            className="input min-h-[88px]"
            value={competitors}
            onChange={(event) => setCompetitors(event.target.value)}
            placeholder={"每行一个，或用逗号分隔\nB001ABC123\nB002DEF456"}
          />
        </div>

        <div>
          <label className="mb-2 block text-sm font-medium" htmlFor="keywords">
            关键词（可选）
          </label>
          <textarea
            id="keywords"
            className="input min-h-[72px]"
            value={keywords}
            onChange={(event) => setKeywords(event.target.value)}
            placeholder="obd2, scanner, diagnostic"
          />
        </div>

        {error ? (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
            {error}
          </div>
        ) : null}

        <div className="flex flex-wrap gap-3">
          <button type="submit" className="btn-primary" disabled={loading || !sku.trim()}>
            {loading ? "创建中..." : "创建并运行"}
          </button>
          <Link href="/tasks" className="btn-secondary">
            取消
          </Link>
        </div>
      </form>
    </AppShell>
  );
}
