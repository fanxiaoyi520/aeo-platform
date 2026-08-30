import { listingFromGenerated, listingToPayload, type ListingDraft } from "@/lib/listing-draft";

export type ListingExportMeta = {
  taskId: string;
  sku: string;
  platform: string;
  market: string;
  listingVersion?: number | null;
};

export function listingFromFinalOutput(
  source: Record<string, unknown> | null | undefined,
): ListingDraft {
  return listingFromGenerated(source);
}

export function listingVersionFromOutput(source: Record<string, unknown> | null | undefined): number | null {
  if (!source) return null;
  const metrics = source.metrics;
  if (typeof metrics === "object" && metrics !== null && "listing_version" in metrics) {
    const version = (metrics as { listing_version?: unknown }).listing_version;
    return typeof version === "number" ? version : null;
  }
  return null;
}

export function formatListingForClipboard(draft: ListingDraft): string {
  const lines = [`Title: ${draft.title.trim()}`];
  draft.bullets.forEach((bullet, index) => {
    const value = bullet.trim();
    if (value) {
      lines.push(`Bullet ${index + 1}: ${value}`);
    }
  });
  if (draft.search_terms.trim()) {
    lines.push(`Search Terms: ${draft.search_terms.trim()}`);
  }
  if (draft.description.trim()) {
    lines.push(`Description: ${draft.description.trim()}`);
  }
  return lines.join("\n");
}

export function buildExportFilename(meta: ListingExportMeta, extension: "json" | "csv"): string {
  const safeSku = meta.sku.replace(/[^\w.-]+/g, "_").slice(0, 64) || "listing";
  const shortId = meta.taskId.slice(0, 8);
  return `${safeSku}-${shortId}-listing.${extension}`;
}

export function listingToJson(meta: ListingExportMeta, draft: ListingDraft): string {
  const payload = {
    task_id: meta.taskId,
    sku: meta.sku,
    platform: meta.platform,
    market: meta.market,
    listing_version: meta.listingVersion ?? null,
    listing: listingToPayload(draft),
    exported_at: new Date().toISOString(),
  };
  return JSON.stringify(payload, null, 2);
}

function escapeCsvCell(value: string): string {
  if (/[",\n\r]/.test(value)) {
    return `"${value.replace(/"/g, '""')}"`;
  }
  return value;
}

export function listingToCsv(meta: ListingExportMeta, draft: ListingDraft): string {
  const bullets = [...draft.bullets];
  while (bullets.length < 5) {
    bullets.push("");
  }
  const row = [
    meta.taskId,
    meta.sku,
    meta.platform,
    meta.market,
    String(meta.listingVersion ?? ""),
    draft.title,
    ...bullets.slice(0, 5).map((bullet) => bullet.trim()),
    draft.search_terms,
    draft.description,
  ].map((cell) => escapeCsvCell(cell));
  const header = [
    "task_id",
    "sku",
    "platform",
    "market",
    "listing_version",
    "title",
    "bullet_1",
    "bullet_2",
    "bullet_3",
    "bullet_4",
    "bullet_5",
    "search_terms",
    "description",
  ].join(",");
  return `${header}\n${row.join(",")}`;
}

export function downloadTextFile(filename: string, content: string, mimeType: string): void {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export async function copyText(text: string): Promise<void> {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return;
  }
  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.style.position = "fixed";
  textarea.style.opacity = "0";
  document.body.appendChild(textarea);
  textarea.select();
  document.execCommand("copy");
  document.body.removeChild(textarea);
}
