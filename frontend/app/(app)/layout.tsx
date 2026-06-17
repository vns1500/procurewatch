import type { ReactNode } from "react";
import { Sidebar } from "@/components/layout/Sidebar";

export default function AppLayout({ children }: { children: ReactNode }) {
  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <Sidebar />
      <main style={{ flex: 1, minWidth: 0, overflow: "auto" }}>
        {children}
      </main>
    </div>
  );
}
