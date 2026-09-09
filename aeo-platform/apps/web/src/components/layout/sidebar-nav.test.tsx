import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { SidebarNav } from "./sidebar-nav";

vi.mock("next/navigation", () => ({
  usePathname: () => "/",
}));

vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

describe("SidebarNav", () => {
  it("renders all navigation items", () => {
    render(<SidebarNav />);

    expect(screen.getByText("仪表盘")).toBeInTheDocument();
    expect(screen.getByText("指标")).toBeInTheDocument();
    expect(screen.getByText("指挥台")).toBeInTheDocument();
    expect(screen.getByText("任务")).toBeInTheDocument();
    expect(screen.getByText("独立站")).toBeInTheDocument();
    expect(screen.getByText("知识库")).toBeInTheDocument();
    expect(screen.getByText("设置")).toBeInTheDocument();
  });

  it("renders links with correct hrefs", () => {
    render(<SidebarNav />);

    const dashboardLink = screen.getByText("仪表盘").closest("a");
    expect(dashboardLink).toHaveAttribute("href", "/");

    const tasksLink = screen.getByText("任务").closest("a");
    expect(tasksLink).toHaveAttribute("href", "/tasks");
  });
});
