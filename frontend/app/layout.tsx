import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/contexts/AuthContext";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "ArmPilot-AI — Arm64-First LLM Inference Optimization & Benchmarking",
  description:
    "Deploy, benchmark, optimize, and compare open-source LLMs on ARM64 infrastructure. CPU-efficient AI inference with real-time telemetry and micro-benchmarking.",
  keywords: [
    "ARM64",
    "LLM Inference",
    "Benchmarking",
    "Quantization",
    "llama.cpp",
    "Neoverse",
    "SVE2",
    "AI Performance",
  ],
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} dark h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-[#0B0F19] text-[#F3F4F6] selection:bg-[#EA580C]/30 selection:text-white">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
