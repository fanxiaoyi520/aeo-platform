import { Suspense } from "react";

import TasksPageClient from "./tasks-page-client";

export default function TasksPage() {
  return (
    <Suspense
      fallback={
        <div className="p-10 text-sm text-[var(--muted)]">加载任务列表...</div>
      }
    >
      <TasksPageClient />
    </Suspense>
  );
}
