export type TaskStatus =
  | "pending"
  | "running"
  | "waiting_hitl"
  | "completed"
  | "failed";

const STATUS_LABELS: Record<TaskStatus, string> = {
  pending: "待处理",
  running: "运行中",
  waiting_hitl: "待审核",
  completed: "已完成",
  failed: "失败",
};

const STATUS_CLASSES: Record<TaskStatus, string> = {
  pending: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
  running: "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300",
  waiting_hitl: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300",
  completed: "bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300",
  failed: "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300",
};

export function formatTaskStatus(status: string): { label: string; className: string } {
  const key = status as TaskStatus;
  if (key in STATUS_LABELS) {
    return { label: STATUS_LABELS[key], className: STATUS_CLASSES[key] };
  }
  return { label: status, className: STATUS_CLASSES.pending };
}

export function formatPlatform(platform: string): string {
  if (platform === "amazon") return "Amazon";
  if (platform === "tiktok") return "TikTok";
  return platform;
}
