import type { Metadata } from "next";
import { AuthProvider } from "@/contexts/auth-context";
import "./globals.css";

export const metadata: Metadata = {
  title: "AEO Platform Workbench",
  description: "AI ecommerce operations workbench",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
