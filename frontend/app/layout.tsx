import type { Metadata } from "next";
import type { ReactNode } from "react";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "ProcureWatch — Government Procurement Intelligence",
  description: "AI-powered anomaly detection for Indian government procurement. Monitor ₹6.2 lakh crore in contracts across 600+ ministries.",
  openGraph: {
    title: "ProcureWatch — Government Procurement Intelligence",
    description: "AI-powered anomaly detection for Indian government procurement. Monitor ₹6.2 lakh crore in contracts across 600+ ministries.",
    url: "https://procurewatch.in",
    siteName: "ProcureWatch",
    type: "website",
    images: [
      {
        url: "https://procurewatch.in/og-image.png",
        width: 1200,
        height: 630,
        alt: "ProcureWatch — Government Procurement Intelligence",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "ProcureWatch — Government Procurement Intelligence",
    description: "AI-powered anomaly detection for Indian government procurement.",
    images: ["https://procurewatch.in/og-image.png"],
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
