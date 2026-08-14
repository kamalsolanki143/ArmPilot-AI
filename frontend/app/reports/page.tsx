"use client";

import React, { useState } from "react";
import AppLayout from "@/components/AppLayout";
import { MOCK_REPORT_METRICS } from "@/services/mockData";
import {
  FileTextIcon,
  DownloadIcon,
  CheckIcon,
  BarChartIcon,
  ZapIcon,
} from "@/components/Icons";

export default function ReportsPage() {
  const [downloadToast, setDownloadToast] = useState<string | null>(null);

  const reportId = "RUN-0042";
  const modelName = "Llama-3.2-3B";
  const timestamp = "2026-08-11 14:32 UTC";

  const handleExportMarkdown = () => {
    const md = `# ArmPilot-AI Performance Report
**Run ID:** ${reportId}
**Model:** ${modelName}
**Generated:** ${timestamp}
**Target Hardware:** Arm Neoverse N1 (64-core, 128 GB)

## Executive Summary
- **Overall Improvement:** +169% throughput gain
- **Memory Reduction:** -53% (6.4 GB -> 3.2 GB)
- **P95 Latency:** -66% (310ms -> 104ms)

## Detailed Benchmark Telemetry
| Metric | Baseline (FP16) | Optimized (INT4) | Delta | Status |
| :--- | :--- | :--- | :--- | :--- |
${MOCK_REPORT_METRICS.map(
  (r) => `| ${r.metric} | ${r.baseline} | ${r.optimized} | ${r.delta} | ${r.status} |`
).join("\n")}

---
*Report generated automatically by ArmPilot-AI v2.4.1*
`;

    const blob = new Blob([md], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `armpilot-report-${reportId}.md`;
    a.click();

    setDownloadToast("Markdown report downloaded");
    setTimeout(() => setDownloadToast(null), 3000);
  };

  const handleExportHtml = () => {
    const html = `<!DOCTYPE html>
<html>
<head>
  <title>ArmPilot-AI Report - ${reportId}</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #0B0F19; color: #F3F4F6; padding: 40px; }
    h1 { color: #EA580C; }
    table { width: 100%; border-collapse: collapse; margin-top: 20px; font-family: monospace; }
    th, td { border: 1px solid #1F293D; padding: 10px; text-align: left; }
    th { background: #111827; }
    .badge { color: #10B981; font-weight: bold; }
  </style>
</head>
<body>
  <h1>ArmPilot-AI Performance Report</h1>
  <p><strong>Run:</strong> ${reportId} · <strong>Model:</strong> ${modelName} · <strong>Date:</strong> ${timestamp}</p>
  <table>
    <thead><tr><th>Metric</th><th>Baseline</th><th>Optimized</th><th>Delta</th><th>Status</th></tr></thead>
    <tbody>
      ${MOCK_REPORT_METRICS.map(
        (r) =>
          `<tr><td>${r.metric}</td><td>${r.baseline}</td><td>${r.optimized}</td><td class="badge">${r.delta}</td><td>${r.status}</td></tr>`
      ).join("")}
    </tbody>
  </table>
</body>
</html>`;

    const blob = new Blob([html], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `armpilot-report-${reportId}.html`;
    a.click();

    setDownloadToast("HTML report downloaded");
    setTimeout(() => setDownloadToast(null), 3000);
  };

  const handleExportPdf = () => {
    window.print();
  };

  return (
    <AppLayout pageTitle="Performance Report">
      {/* ── Header ── */}
      <div className="pb-2 border-b border-[#1F293D]/60 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Performance Report
          </h1>
          <p className="text-xs sm:text-sm text-zinc-400 font-mono mt-1">
            {reportId} · {modelName} · {timestamp}
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2.5">
          <button
            onClick={handleExportMarkdown}
            className="px-3 py-1.5 rounded-lg bg-[#162032] hover:bg-[#1E293D] text-zinc-200 text-xs font-mono font-medium border border-[#1F293D] flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            <DownloadIcon className="w-3.5 h-3.5 text-zinc-400" />
            Export Markdown
          </button>

          <button
            onClick={handleExportHtml}
            className="px-3 py-1.5 rounded-lg bg-[#162032] hover:bg-[#1E293D] text-zinc-200 text-xs font-mono font-medium border border-[#1F293D] flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            <DownloadIcon className="w-3.5 h-3.5 text-zinc-400" />
            Export HTML
          </button>

          <button
            onClick={handleExportPdf}
            className="px-4 py-1.5 rounded-lg bg-[#EA580C] hover:bg-[#FF7315] text-white text-xs font-mono font-bold shadow-lg shadow-orange-600/20 flex items-center gap-1.5 transition-all cursor-pointer"
          >
            <DownloadIcon className="w-3.5 h-3.5" />
            Export PDF
          </button>
        </div>
      </div>

      {downloadToast && (
        <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-mono flex items-center gap-2">
          <CheckIcon className="w-4 h-4" />
          <span>{downloadToast}</span>
        </div>
      )}

      {/* ── Executive Summary (3 Big Metric Cards) ── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="rounded-xl bg-[#111827] border border-emerald-500/30 p-5 text-center">
          <span className="text-xs font-mono uppercase tracking-wider text-zinc-400 block mb-1">
            Overall Improvement
          </span>
          <span className="text-3xl font-bold font-mono text-emerald-400">
            +169%
          </span>
          <span className="text-xs font-sans text-zinc-400 block mt-1">
            Throughput gain vs FP16 baseline
          </span>
        </div>

        <div className="rounded-xl bg-[#111827] border border-cyan-500/30 p-5 text-center">
          <span className="text-xs font-mono uppercase tracking-wider text-zinc-400 block mb-1">
            Memory Reduction
          </span>
          <span className="text-3xl font-bold font-mono text-cyan-400">
            -53%
          </span>
          <span className="text-xs font-sans text-zinc-400 block mt-1">
            6.4 GB → 3.2 GB working set
          </span>
        </div>

        <div className="rounded-xl bg-[#111827] border border-orange-500/30 p-5 text-center">
          <span className="text-xs font-mono uppercase tracking-wider text-zinc-400 block mb-1">
            Latency (P95)
          </span>
          <span className="text-3xl font-bold font-mono text-orange-400">
            -66%
          </span>
          <span className="text-xs font-sans text-zinc-400 block mt-1">
            310ms → 104ms
          </span>
        </div>
      </div>

      {/* ── Before vs After — Throughput Bar Chart Comparison ── */}
      <div className="rounded-xl bg-[#111827] border border-[#1F293D] p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-sm font-bold text-white tracking-wide">
              Throughput Comparison (Tokens / Sec)
            </h2>
            <p className="text-xs text-zinc-400 font-mono">FP16 Baseline vs INT4 + Arm SVE2 Optimized</p>
          </div>
          <span className="text-xs font-mono text-emerald-400 font-bold">+2.69× speedup</span>
        </div>

        {/* Horizontal Comparative Bar Chart */}
        <div className="space-y-4 pt-2">
          {/* Baseline Bar */}
          <div>
            <div className="flex justify-between text-xs font-mono mb-1.5">
              <span className="text-zinc-400">FP16 Baseline (Single Thread, Unpinned)</span>
              <span className="text-orange-400 font-bold">12.9 tok/sec</span>
            </div>
            <div className="w-full bg-[#0B0F19] rounded-full h-5 overflow-hidden border border-[#1F293D]">
              <div
                className="bg-orange-500 h-full rounded-full flex items-center justify-end pr-2 text-[10px] font-mono text-white font-bold"
                style={{ width: "37%" }}
              >
                12.9
              </div>
            </div>
          </div>

          {/* Optimized Bar */}
          <div>
            <div className="flex justify-between text-xs font-mono mb-1.5">
              <span className="text-zinc-300 font-semibold">INT4 + SVE2 + 32 Threads Pinned</span>
              <span className="text-emerald-400 font-bold">34.7 tok/sec</span>
            </div>
            <div className="w-full bg-[#0B0F19] rounded-full h-5 overflow-hidden border border-[#1F293D]">
              <div
                className="bg-gradient-to-r from-emerald-600 to-emerald-400 h-full rounded-full flex items-center justify-end pr-2 text-[10px] font-mono text-white font-bold"
                style={{ width: "100%" }}
              >
                34.7
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Detailed Metrics — Before vs After Table ── */}
      <div className="rounded-xl bg-[#111827] border border-[#1F293D] overflow-hidden">
        <div className="p-4 sm:p-5 border-b border-[#1F293D]">
          <h2 className="text-base font-bold text-white">Detailed Telemetry Breakdown</h2>
          <p className="text-xs text-zinc-400 font-mono">
            Granular benchmark delta verification across all evaluation parameters
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-[#0E1422] text-zinc-400 border-b border-[#1F293D] uppercase text-[11px]">
              <tr>
                <th className="py-3.5 px-4 font-semibold">Metric</th>
                <th className="py-3.5 px-4 font-semibold">Baseline (FP16)</th>
                <th className="py-3.5 px-4 font-semibold">Optimized (INT4)</th>
                <th className="py-3.5 px-4 font-semibold">Delta</th>
                <th className="py-3.5 px-4 font-semibold">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1F293D]/60 text-zinc-300">
              {MOCK_REPORT_METRICS.map((row, idx) => (
                <tr key={idx} className="hover:bg-[#162032] transition-colors">
                  <td className="py-3.5 px-4 font-bold text-white">{row.metric}</td>
                  <td className="py-3.5 px-4 text-zinc-400">{row.baseline}</td>
                  <td className="py-3.5 px-4 font-semibold text-white">{row.optimized}</td>
                  <td className="py-3.5 px-4 font-bold text-emerald-400">{row.delta}</td>
                  <td className="py-3.5 px-4">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                      {row.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </AppLayout>
  );
}
