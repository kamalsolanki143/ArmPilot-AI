"use client";

import React, { useState, useEffect } from "react";
import AppLayout from "@/components/AppLayout";
import { MOCK_MODELS } from "@/services/mockData";
import { apiService } from "@/services/api";
import {
  GaugeIcon,
  PlayIcon,
  CheckIcon,
  RefreshIcon,
  ActivityIcon,
  AlertTriangleIcon,
  DownloadIcon,
} from "@/components/Icons";

export default function BenchmarkRunnerPage() {
  const [selectedModel, setSelectedModel] = useState(MOCK_MODELS[0].id);
  const [concurrency, setConcurrency] = useState(4);
  const [duration, setDuration] = useState(60);
  const [promptStrategy, setPromptStrategy] = useState<"fixed" | "synthetic" | "file">("fixed");

  // Run status state
  const [status, setStatus] = useState<"IDLE" | "RUNNING" | "COMPLETE">("IDLE");
  const [progress, setProgress] = useState(0);
  const [elapsed, setElapsed] = useState(0);

  // Result metrics
  const [results, setResults] = useState({
    ttft: 48,
    tps: 34.7,
    p95: 104,
    cpuUtil: 84,
  });

  // Simulated live CPU utilization line
  const [cpuHistory, setCpuHistory] = useState<number[]>([
    28, 42, 65, 84, 88, 86, 84, 82, 85, 84,
  ]);

  const handleStartBenchmark = async () => {
    if (status === "RUNNING") return;

    setStatus("RUNNING");
    setProgress(0);
    setElapsed(0);

    const totalSteps = 40;
    const intervalMs = 100; // Fast and smooth for live demo responsiveness

    let currentStep = 0;
    const timer = setInterval(() => {
      currentStep++;
      const currentProgress = Math.min(100, Math.round((currentStep / totalSteps) * 100));
      const currentElapsed = Math.min(duration, Math.round((currentStep / totalSteps) * duration));

      setProgress(currentProgress);
      setElapsed(currentElapsed);

      // Random fluctuating live CPU between 78% and 94%
      setCpuHistory((prev) => [
        ...prev.slice(1),
        Math.floor(Math.random() * 16 + 78),
      ]);

      if (currentStep >= totalSteps) {
        clearInterval(timer);
        setStatus("COMPLETE");
        setResults({
          ttft: 48,
          tps: +(34.7 + (Math.random() * 2 - 1)).toFixed(1),
          p95: Math.floor(104 + (Math.random() * 6 - 3)),
          cpuUtil: 84,
        });
      }
    }, intervalMs);
  };

  return (
    <AppLayout pageTitle="Benchmark Runner">
      {/* ── Header ── */}
      <div className="pb-2 border-b border-[#1F293D]/60">
        <h1 className="text-2xl font-bold tracking-tight text-white">
          Benchmark Runner
        </h1>
        <p className="text-xs sm:text-sm text-zinc-400 font-mono mt-1">
          Configure and execute micro-benchmarks with hardware-level telemetry
        </p>
      </div>

      {/* ── Two Column Grid: Config Panel (Left) & Live Telemetry (Right) ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Panel: Configuration (5 cols) */}
        <div className="lg:col-span-5 rounded-xl bg-[#111827] border border-[#1F293D] p-5 space-y-5">
          <div className="flex items-center justify-between border-b border-[#1F293D] pb-3">
            <h2 className="text-sm font-bold text-white tracking-wide">
              Configuration
            </h2>
            <span className="text-[11px] font-mono text-zinc-400">Arm Neoverse N1</span>
          </div>

          {/* Model selection dropdown */}
          <div>
            <label className="block text-xs font-mono text-zinc-400 uppercase tracking-wider mb-2 font-semibold">
              Target Model
            </label>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="w-full rounded-lg bg-[#0B0F19] border border-[#1F293D] px-3.5 py-2.5 text-sm text-zinc-200 font-mono focus:outline-none focus:border-orange-500 transition-colors"
            >
              {MOCK_MODELS.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name} ({m.quantization} · {m.size})
                </option>
              ))}
            </select>
          </div>

          {/* Concurrency Slider */}
          <div>
            <div className="flex justify-between text-xs font-mono mb-2">
              <span className="text-zinc-400 uppercase tracking-wider font-semibold">Concurrency</span>
              <span className="text-orange-400 font-bold">{concurrency} workers</span>
            </div>
            <input
              type="range"
              min="1"
              max="32"
              step="1"
              value={concurrency}
              onChange={(e) => setConcurrency(Number(e.target.value))}
              className="w-full cursor-pointer h-2 bg-[#0B0F19] rounded-lg appearance-none"
            />
            <div className="flex justify-between text-[10px] font-mono text-zinc-400 mt-1">
              <span>1</span>
              <span>8</span>
              <span>16</span>
              <span>32</span>
            </div>
          </div>

          {/* Duration Slider */}
          <div>
            <div className="flex justify-between text-xs font-mono mb-2">
              <span className="text-zinc-400 uppercase tracking-wider font-semibold">Duration</span>
              <span className="text-orange-400 font-bold">{duration}s</span>
            </div>
            <input
              type="range"
              min="10"
              max="300"
              step="10"
              value={duration}
              onChange={(e) => setDuration(Number(e.target.value))}
              className="w-full cursor-pointer h-2 bg-[#0B0F19] rounded-lg appearance-none"
            />
            <div className="flex justify-between text-[10px] font-mono text-zinc-400 mt-1">
              <span>10s</span>
              <span>60s</span>
              <span>180s</span>
              <span>300s</span>
            </div>
          </div>

          {/* Prompt Strategy Radio Group */}
          <div>
            <label className="block text-xs font-mono text-zinc-400 uppercase tracking-wider mb-2 font-semibold">
              Prompt Strategy
            </label>
            <div className="space-y-2">
              {[
                { id: "fixed", label: "Fixed prompt (128 tokens)", desc: "Deterministic baseline comparison" },
                { id: "synthetic", label: "Random synthetic prompts", desc: "Variable context lengths" },
                { id: "file", label: "Custom prompt dataset", desc: "Load from JSONL / CSV" },
              ].map((opt) => (
                <label
                  key={opt.id}
                  className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-all ${
                    promptStrategy === opt.id
                      ? "bg-[#1E293B]/70 border-orange-500/80 ring-1 ring-orange-500/40"
                      : "bg-[#0B0F19] border-[#1F293D] hover:border-zinc-500"
                  }`}
                >
                  <input
                    type="radio"
                    name="strategy"
                    checked={promptStrategy === opt.id}
                    onChange={() => setPromptStrategy(opt.id as any)}
                    className="mt-0.5 text-orange-500 focus:ring-orange-500"
                  />
                  <div>
                    <div className="text-xs font-bold text-white font-mono">{opt.label}</div>
                    <div className="text-[11px] text-zinc-400 font-sans">{opt.desc}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Start Benchmark CTA Button */}
          <div className="pt-2">
            <button
              onClick={handleStartBenchmark}
              disabled={status === "RUNNING"}
              className="w-full py-3 rounded-lg bg-[#EA580C] hover:bg-[#FF7315] disabled:opacity-75 text-white font-bold text-sm shadow-lg shadow-orange-600/25 flex items-center justify-center gap-2 transition-all hover:scale-[1.01] cursor-pointer"
            >
              {status === "RUNNING" ? (
                <>
                  <RefreshIcon className="w-4 h-4 animate-spin" />
                  <span>Running... {progress}%</span>
                </>
              ) : (
                <>
                  <PlayIcon className="w-4 h-4" />
                  <span>{status === "COMPLETE" ? "▶ Run Again" : "▶ Start Benchmark"}</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Right Panel: Progress, Real-Time Metrics & CPU Utilization (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          {/* Progress Card */}
          <div className="rounded-xl bg-[#111827] border border-[#1F293D] p-5">
            <div className="flex items-center justify-between mb-3">
              <div>
                <span className="text-xs font-mono uppercase tracking-wider text-zinc-400 font-semibold">
                  Execution Status
                </span>
                <div className="text-sm font-mono text-zinc-200 mt-0.5">
                  {status === "IDLE" && "Ready to execute"}
                  {status === "RUNNING" && `${elapsed}s / ${duration}s elapsed (${progress}%)`}
                  {status === "COMPLETE" && `Completed in ${duration}s · PASS`}
                </div>
              </div>

              <div>
                {status === "IDLE" && (
                  <span className="px-2.5 py-1 rounded text-xs font-mono bg-zinc-800 text-zinc-400 border border-zinc-700">
                    IDLE
                  </span>
                )}
                {status === "RUNNING" && (
                  <span className="px-2.5 py-1 rounded text-xs font-mono bg-orange-500/20 text-orange-400 border border-orange-500/40 font-bold flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-orange-400 animate-pulse" />
                    RUNNING
                  </span>
                )}
                {status === "COMPLETE" && (
                  <span className="px-2.5 py-1 rounded text-xs font-mono bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 font-bold flex items-center gap-1.5">
                    <CheckIcon className="w-3.5 h-3.5" />
                    COMPLETE
                  </span>
                )}
              </div>
            </div>

            {/* Visual Progress Bar */}
            <div className="w-full bg-[#0B0F19] rounded-full h-3 overflow-hidden border border-[#1F293D]">
              <div
                className="bg-gradient-to-r from-orange-600 to-amber-400 h-full rounded-full transition-all duration-150"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>

          {/* Results Metric Cards (Visible after or during run) */}
          <div className="grid grid-cols-3 gap-3">
            <div className="rounded-xl bg-[#111827] border border-cyan-500/30 p-4 text-center">
              <span className="text-[11px] font-mono uppercase tracking-wider text-zinc-400 block mb-1">
                TTFT
              </span>
              <span className="text-2xl font-bold font-mono text-cyan-400">
                {status !== "IDLE" ? results.ttft : "--"}
                <span className="text-xs font-normal text-zinc-400 ml-1">ms</span>
              </span>
              <span className="text-[10px] font-mono text-emerald-400 block mt-1">
                -62% vs baseline
              </span>
            </div>

            <div className="rounded-xl bg-[#111827] border border-emerald-500/30 p-4 text-center">
              <span className="text-[11px] font-mono uppercase tracking-wider text-zinc-400 block mb-1">
                TOKENS / SEC
              </span>
              <span className="text-2xl font-bold font-mono text-emerald-400">
                {status !== "IDLE" ? results.tps : "--"}
              </span>
              <span className="text-[10px] font-mono text-emerald-400 block mt-1">
                +169% vs baseline
              </span>
            </div>

            <div className="rounded-xl bg-[#111827] border border-orange-500/30 p-4 text-center">
              <span className="text-[11px] font-mono uppercase tracking-wider text-zinc-400 block mb-1">
                P95 LATENCY
              </span>
              <span className="text-2xl font-bold font-mono text-orange-400">
                {status !== "IDLE" ? results.p95 : "--"}
                <span className="text-xs font-normal text-zinc-400 ml-1">ms</span>
              </span>
              <span className="text-[10px] font-mono text-emerald-400 block mt-1">
                -66% vs baseline
              </span>
            </div>
          </div>

          {/* CPU Utilization (%) Telemetry Graph */}
          <div className="rounded-xl bg-[#111827] border border-[#1F293D] p-5">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-bold text-white tracking-wide">
                  CPU Utilization (%)
                </h3>
                <p className="text-xs text-zinc-400 font-mono">
                  64 Arm Neoverse N1 physical cores
                </p>
              </div>

              <div className="text-xs font-mono text-orange-400 font-bold">
                {status === "RUNNING"
                  ? `${cpuHistory[cpuHistory.length - 1]}% Active`
                  : status === "COMPLETE"
                  ? "84% Average"
                  : "0% Idle"}
              </div>
            </div>

            {/* SVG Real-time Area Chart */}
            <div className="h-44 w-full">
              <svg viewBox="0 0 500 150" className="w-full h-full overflow-visible">
                <defs>
                  <linearGradient id="cpuGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#EA580C" stopOpacity="0.3" />
                    <stop offset="100%" stopColor="#EA580C" stopOpacity="0" />
                  </linearGradient>
                </defs>

                {/* Grid */}
                <line x1="35" y1="20" x2="480" y2="20" stroke="#1F293D" strokeDasharray="3 3" />
                <line x1="35" y1="70" x2="480" y2="70" stroke="#1F293D" strokeDasharray="3 3" />
                <line x1="35" y1="120" x2="480" y2="120" stroke="#1F293D" />

                <text x="25" y="24" fill="#6B7280" fontSize="10" textAnchor="end" fontFamily="monospace">100%</text>
                <text x="25" y="74" fill="#6B7280" fontSize="10" textAnchor="end" fontFamily="monospace">50%</text>
                <text x="25" y="124" fill="#6B7280" fontSize="10" textAnchor="end" fontFamily="monospace">0%</text>

                {/* Polyline / Polygon points */}
                {(() => {
                  const pts = cpuHistory.map((val, idx) => {
                    const x = 40 + idx * 48;
                    const y = 120 - (val / 100) * 100;
                    return `${x},${y}`;
                  });
                  const polylineStr = pts.join(" ");
                  const polygonStr = `${pts[0].split(",")[0]},120 ${polylineStr} ${pts[pts.length - 1].split(",")[0]},120`;

                  return (
                    <>
                      <polygon points={polygonStr} fill="url(#cpuGrad)" />
                      <polyline fill="none" stroke="#EA580C" strokeWidth="2.5" points={polylineStr} />
                      {cpuHistory.map((val, idx) => {
                        const x = 40 + idx * 48;
                        const y = 120 - (val / 100) * 100;
                        return <circle key={idx} cx={x} cy={y} r="3" fill="#FF7315" />;
                      })}
                    </>
                  );
                })()}
              </svg>
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
