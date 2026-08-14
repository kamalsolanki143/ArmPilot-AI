"use client";

import React, { useState } from "react";
import Link from "next/link";
import AppLayout from "@/components/AppLayout";
import {
  INITIAL_METRICS,
  MOCK_RUNS,
  MetricCardData,
  RunRecord,
} from "@/services/mockData";
import {
  GaugeIcon,
  PlayIcon,
  ZapIcon,
  ArrowRightIcon,
  RefreshIcon,
  CheckIcon,
  AlertTriangleIcon,
} from "@/components/Icons";

export default function DashboardPage() {
  const [metrics] = useState<MetricCardData[]>(INITIAL_METRICS);
  const [runs] = useState<RunRecord[]>(MOCK_RUNS.slice(0, 5));
  const [activeChartFilter, setActiveChartFilter] = useState<"1h" | "6h" | "24h">("24h");

  // Throughput Data points (Baseline vs Optimized)
  const throughputData = [
    { time: "00:00", baseline: 12.1, optimized: 32.4 },
    { time: "04:00", baseline: 12.8, optimized: 33.8 },
    { time: "08:00", baseline: 11.9, optimized: 35.1 },
    { time: "12:00", baseline: 13.4, optimized: 36.2 },
    { time: "16:00", baseline: 12.6, optimized: 34.0 },
    { time: "20:00", baseline: 12.9, optimized: 34.7 },
  ];

  // Latency Distribution percentiles (P50, P95, P99)
  const latencyData = [
    { concurrency: "c=1", p50: 42, p95: 78, p99: 112 },
    { concurrency: "c=4", p50: 55, p95: 94, p99: 138 },
    { concurrency: "c=8", p50: 62, p95: 104, p99: 162 },
    { concurrency: "c=16", p50: 74, p95: 132, p99: 198 },
    { concurrency: "c=32", p50: 98, p95: 184, p99: 275 },
  ];

  return (
    <AppLayout pageTitle="Dashboard">
      {/* ── Top Section ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-[#1F293D]/60">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-white">
              System Overview
            </h1>
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-status-pulse" />
              Inference Server Online
            </span>
          </div>
          <p className="text-xs sm:text-sm text-zinc-400 font-mono mt-1">
            Arm Neoverse N1 · 64-core · 128 GB · ArmPilot v2.4.1
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/inference"
            className="px-3.5 py-2 rounded-lg bg-[#162032] hover:bg-[#1E293D] text-zinc-200 hover:text-white text-xs sm:text-sm font-medium border border-[#1F293D] flex items-center gap-2 transition-colors"
          >
            <PlayIcon className="w-3.5 h-3.5 text-zinc-400" />
            Run Test
          </Link>

          <Link
            href="/benchmarks"
            className="px-4 py-2 rounded-lg bg-[#EA580C] hover:bg-[#FF7315] text-white text-xs sm:text-sm font-semibold shadow-lg shadow-orange-600/20 flex items-center gap-2 transition-all hover:scale-[1.02]"
          >
            <GaugeIcon className="w-4 h-4" />
            + New Benchmark
          </Link>
        </div>
      </div>

      {/* ── 8 Metrics Grid ── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
        {metrics.map((card, idx) => {
          let valueColorClass = "text-white";
          let borderAccentClass = "border-[#1F293D]";

          if (card.color === "cyan") {
            valueColorClass = "text-[#06B6D4]";
            borderAccentClass = "border-cyan-500/20 hover:border-cyan-500/40";
          } else if (card.color === "green") {
            valueColorClass = "text-[#10B981]";
            borderAccentClass = "border-emerald-500/20 hover:border-emerald-500/40";
          } else if (card.color === "orange") {
            valueColorClass = "text-[#F97316]";
            borderAccentClass = "border-orange-500/20 hover:border-orange-500/40";
          } else if (card.color === "purple") {
            valueColorClass = "text-[#A855F7]";
            borderAccentClass = "border-purple-500/20 hover:border-purple-500/40";
          }

          return (
            <div
              key={idx}
              className={`rounded-xl bg-[#111827] border ${borderAccentClass} p-4 transition-all duration-200 hover:-translate-y-0.5 shadow-sm`}
            >
              <div className="flex items-center justify-between text-xs font-mono text-zinc-400 tracking-wider uppercase mb-2">
                <span>{card.title}</span>
                {card.color === "cyan" && <span className="w-1.5 h-1.5 rounded-full bg-[#06B6D4]" />}
                {card.color === "green" && <span className="w-1.5 h-1.5 rounded-full bg-[#10B981]" />}
                {card.color === "orange" && <span className="w-1.5 h-1.5 rounded-full bg-[#F97316]" />}
                {card.color === "purple" && <span className="w-1.5 h-1.5 rounded-full bg-[#A855F7]" />}
              </div>

              <div className="flex items-baseline gap-1.5 mb-1.5">
                <span className={`text-2xl lg:text-3xl font-bold tracking-tight font-mono ${valueColorClass}`}>
                  {card.value}
                </span>
                {card.unit && (
                  <span className="text-xs font-mono text-zinc-400">{card.unit}</span>
                )}
              </div>

              <div className="flex items-center justify-between text-xs">
                <span
                  className={`font-mono font-medium ${
                    card.change.includes("+")
                      ? "text-emerald-400"
                      : card.change.includes("-")
                      ? "text-orange-400"
                      : "text-zinc-400"
                  }`}
                >
                  {card.change}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* ── Two Live Charts ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Chart 1: Throughput Before vs After */}
        <div className="rounded-xl bg-[#111827] border border-[#1F293D] p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-bold text-white tracking-wide">
                Throughput — Before vs After
              </h2>
              <p className="text-xs text-zinc-400 font-mono">Tokens / Second over 24-hour evaluation window</p>
            </div>
            <div className="flex items-center gap-3 text-xs font-mono">
              <span className="flex items-center gap-1 text-emerald-400">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                Optimized (34.7)
              </span>
              <span className="flex items-center gap-1 text-orange-400">
                <span className="w-2.5 h-2.5 rounded-full bg-orange-500" />
                Baseline (12.9)
              </span>
            </div>
          </div>

          {/* SVG Line Chart */}
          <div className="h-52 w-full pt-2">
            <svg viewBox="0 0 500 180" className="w-full h-full overflow-visible">
              <defs>
                <linearGradient id="optGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#10B981" stopOpacity="0.25" />
                  <stop offset="100%" stopColor="#10B981" stopOpacity="0" />
                </linearGradient>
                <linearGradient id="baseGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#F97316" stopOpacity="0.15" />
                  <stop offset="100%" stopColor="#F97316" stopOpacity="0" />
                </linearGradient>
              </defs>

              {/* Grid lines */}
              <line x1="40" y1="20" x2="480" y2="20" stroke="#1F293D" strokeDasharray="3 3" />
              <line x1="40" y1="65" x2="480" y2="65" stroke="#1F293D" strokeDasharray="3 3" />
              <line x1="40" y1="110" x2="480" y2="110" stroke="#1F293D" strokeDasharray="3 3" />
              <line x1="40" y1="150" x2="480" y2="150" stroke="#1F293D" />

              {/* Y Axis Labels */}
              <text x="30" y="24" fill="#6B7280" fontSize="10" textAnchor="end" fontFamily="monospace">40</text>
              <text x="30" y="69" fill="#6B7280" fontSize="10" textAnchor="end" fontFamily="monospace">25</text>
              <text x="30" y="114" fill="#6B7280" fontSize="10" textAnchor="end" fontFamily="monospace">15</text>
              <text x="30" y="154" fill="#6B7280" fontSize="10" textAnchor="end" fontFamily="monospace">0</text>

              {/* Baseline Area & Line */}
              <polygon
                points="50,118 135,115 220,120 305,112 390,116 475,115 475,150 50,150"
                fill="url(#baseGrad)"
              />
              <polyline
                fill="none"
                stroke="#F97316"
                strokeWidth="2.5"
                points="50,118 135,115 220,120 305,112 390,116 475,115"
              />

              {/* Optimized Area & Line */}
              <polygon
                points="50,38 135,32 220,28 305,24 390,31 475,29 475,150 50,150"
                fill="url(#optGrad)"
              />
              <polyline
                fill="none"
                stroke="#10B981"
                strokeWidth="3"
                points="50,38 135,32 220,28 305,24 390,31 475,29"
              />

              {/* Data points */}
              {throughputData.map((d, i) => {
                const x = 50 + i * 85;
                return (
                  <g key={i}>
                    <circle cx={x} cy={38 - (d.optimized - 32) * 2.8} r="4" fill="#10B981" />
                    <circle cx={x} cy={118 - (d.baseline - 12) * 4} r="3.5" fill="#F97316" />
                    <text x={x} y="168" fill="#6B7280" fontSize="10" textAnchor="middle" fontFamily="monospace">
                      {d.time}
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>
        </div>

        {/* Chart 2: Latency Distribution */}
        <div className="rounded-xl bg-[#111827] border border-[#1F293D] p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-bold text-white tracking-wide">
                Latency Distribution (ms)
              </h2>
              <p className="text-xs text-zinc-400 font-mono">Response percentiles vs concurrency scale</p>
            </div>
            <div className="flex items-center gap-3 text-xs font-mono">
              <span className="flex items-center gap-1 text-cyan-400">
                <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
                P50
              </span>
              <span className="flex items-center gap-1 text-orange-400">
                <span className="w-2.5 h-2.5 rounded-full bg-orange-400" />
                P95
              </span>
              <span className="flex items-center gap-1 text-purple-400">
                <span className="w-2.5 h-2.5 rounded-full bg-purple-400" />
                P99
              </span>
            </div>
          </div>

          {/* SVG Line Chart */}
          <div className="h-52 w-full pt-2">
            <svg viewBox="0 0 500 180" className="w-full h-full overflow-visible">
              {/* Grid lines */}
              <line x1="40" y1="20" x2="480" y2="20" stroke="#1F293D" strokeDasharray="3 3" />
              <line x1="40" y1="65" x2="480" y2="65" stroke="#1F293D" strokeDasharray="3 3" />
              <line x1="40" y1="110" x2="480" y2="110" stroke="#1F293D" strokeDasharray="3 3" />
              <line x1="40" y1="150" x2="480" y2="150" stroke="#1F293D" />

              {/* Y Axis Labels */}
              <text x="30" y="24" fill="#6B7280" fontSize="10" textAnchor="end" fontFamily="monospace">300ms</text>
              <text x="30" y="69" fill="#6B7280" fontSize="10" textAnchor="end" fontFamily="monospace">200ms</text>
              <text x="30" y="114" fill="#6B7280" fontSize="10" textAnchor="end" fontFamily="monospace">100ms</text>
              <text x="30" y="154" fill="#6B7280" fontSize="10" textAnchor="end" fontFamily="monospace">0</text>

              {/* P99 (Purple) */}
              <polyline
                fill="none"
                stroke="#A855F7"
                strokeWidth="2.5"
                points="50,110 155,98 260,86 365,70 470,30"
              />

              {/* P95 (Orange) */}
              <polyline
                fill="none"
                stroke="#F97316"
                strokeWidth="2.5"
                points="50,124 155,116 260,110 365,96 470,68"
              />

              {/* P50 (Cyan) */}
              <polyline
                fill="none"
                stroke="#06B6D4"
                strokeWidth="2.5"
                points="50,138 155,132 260,128 365,122 470,110"
              />

              {/* Data points and X labels */}
              {latencyData.map((d, i) => {
                const x = 50 + i * 105;
                return (
                  <g key={i}>
                    <circle cx={x} cy={138 - i * 7} r="3.5" fill="#06B6D4" />
                    <circle cx={x} cy={124 - i * 14} r="3.5" fill="#F97316" />
                    <circle cx={x} cy={110 - i * 20} r="3.5" fill="#A855F7" />
                    <text x={x} y="168" fill="#6B7280" fontSize="10" textAnchor="middle" fontFamily="monospace">
                      {d.concurrency}
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>
        </div>
      </div>

      {/* ── Recent Benchmark Runs (Table) ── */}
      <div className="rounded-xl bg-[#111827] border border-[#1F293D] overflow-hidden">
        <div className="p-4 sm:p-5 border-b border-[#1F293D] flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-white">Recent Benchmark Runs</h2>
            <p className="text-xs text-zinc-400 font-mono">Real-time inference profiling logs</p>
          </div>

          <Link
            href="/history"
            className="text-xs font-mono font-medium text-orange-400 hover:text-orange-300 flex items-center gap-1 transition-colors"
          >
            View All Runs →
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-[#0E1422] text-zinc-400 border-b border-[#1F293D] uppercase text-[11px]">
              <tr>
                <th className="py-3 px-4 font-semibold">Run ID</th>
                <th className="py-3 px-4 font-semibold">Model</th>
                <th className="py-3 px-4 font-semibold">Configuration</th>
                <th className="py-3 px-4 font-semibold">TTFT</th>
                <th className="py-3 px-4 font-semibold">Tokens / Sec</th>
                <th className="py-3 px-4 font-semibold">P95 Latency</th>
                <th className="py-3 px-4 font-semibold">Status</th>
                <th className="py-3 px-4 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1F293D]/60 text-zinc-300">
              {runs.map((run) => (
                <tr
                  key={run.id}
                  className="hover:bg-[#162032] transition-colors duration-150"
                >
                  <td className="py-3.5 px-4 font-bold text-white flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-orange-500" />
                    {run.id}
                  </td>
                  <td className="py-3.5 px-4 font-sans font-medium text-white">
                    {run.model}
                  </td>
                  <td className="py-3.5 px-4 text-zinc-300">{run.config}</td>
                  <td className="py-3.5 px-4 text-cyan-400 font-semibold">{run.ttft}</td>
                  <td className="py-3.5 px-4 text-emerald-400 font-semibold">{run.tps}</td>
                  <td className="py-3.5 px-4 text-orange-400 font-semibold">{run.p95}</td>
                  <td className="py-3.5 px-4">
                    {run.status === "PASS" ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                        PASS
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/15 text-rose-400 border border-rose-500/30">
                        FAIL
                      </span>
                    )}
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <Link
                      href="/reports"
                      className="text-zinc-400 hover:text-white text-[11px] underline underline-offset-4"
                    >
                      Report →
                    </Link>
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
