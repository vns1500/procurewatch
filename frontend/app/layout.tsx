import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "ProcureWatch — Government Procurement Intelligence",
  description: "Real-time anomaly detection for Indian government procurement",
};

export default function RootLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <div style={{ display: "flex", minHeight: "100vh" }}>
          <Sidebar />
          <main style={{ flex: 1, minWidth: 0, overflow: "auto" }}>
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
