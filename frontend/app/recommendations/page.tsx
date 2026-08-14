"use client";

import React, { useState } from "react";
import AppLayout from "@/components/AppLayout";
import {
  SparklesIcon,
  AlertTriangleIcon,
  CheckIcon,
  ZapIcon,
  DownloadIcon,
  CopyIcon,
  LayersIcon,
  CpuChipIcon,
} from "@/components/Icons";

export default function RecommendationsPage() {
  const [applied, setApplied] = useState(false);
  const [jsonModalOpen, setJsonModalOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  const recommendedJson = {
    model: "Llama-3.2-3B",
    quantization: "INT4_GGUF_Q4_K_M",
    batch_size: 8,
    threads: 32,
    cpu_affinity: "numa_pinned",
    kv_cache: "quantized_q8_0",
    runtime: "llama.cpp_v0.3.8",
    target_hardware: "arm_neoverse_n1_64c",
    optimizations: {
      sve2_vectorization: true,
      neon_dotprod: true,
      numa_interleaving: true,
    },
  };

  const handleCopyJson = () => {
    navigator.clipboard.writeText(JSON.stringify(recommendedJson, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleApply = () => {
    setApplied(true);
    setTimeout(() => setApplied(false), 4000);
  };

  return (
    <AppLayout pageTitle="AI Recommendations">
      {/* ── Header ── */}
      <div className="pb-2 border-b border-[#1F293D]/60 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            AI Recommendations
          </h1>
          <p className="text-xs sm:text-sm text-zinc-400 font-mono mt-1">
            Automated analysis and configuration suggestions based on runtime telemetry
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setJsonModalOpen(true)}
            className="px-3.5 py-2 rounded-lg bg-[#162032] hover:bg-[#1E293D] text-zinc-200 hover:text-white text-xs font-mono font-medium border border-[#1F293D] flex items-center gap-2 transition-colors cursor-pointer"
          >
            <DownloadIcon className="w-3.5 h-3.5" />
            Export Config JSON
          </button>

          <button
            onClick={handleApply}
            className="px-4 py-2 rounded-lg bg-[#EA580C] hover:bg-[#FF7315] text-white text-xs sm:text-sm font-bold shadow-lg shadow-orange-600/25 flex items-center gap-2 transition-all hover:scale-[1.02] cursor-pointer"
          >
            <ZapIcon className="w-4 h-4" />
            ⚡ Apply Recommendation
          </button>
        </div>
      </div>

      {applied && (
        <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-mono flex items-center gap-2 animate-fadeIn">
          <CheckIcon className="w-4 h-4" />
          <span>
            Recommended configuration applied to live runtime environment (Llama-3.2-3B INT4, batch=8, threads=32).
          </span>
        </div>
      )}

      {/* ── Alert Banner: Detected Bottleneck ── */}
      <div className="rounded-xl bg-gradient-to-r from-[#2A1608] to-[#1E1510] border border-orange-500/40 p-5 shadow-lg shadow-orange-950/20">
        <div className="flex items-start gap-3.5">
          <div className="p-2 rounded-lg bg-orange-500/20 text-orange-400 border border-orange-500/30 shrink-0">
            <AlertTriangleIcon className="w-5 h-5" />
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-orange-400">
                Detected Bottleneck
              </span>
              <span className="text-xs font-mono text-zinc-400">· Critical Impact</span>
            </div>

            <p className="text-xs sm:text-sm text-zinc-200 leading-relaxed font-sans">
              Memory bandwidth saturation detected at <span className="font-bold text-orange-300">92.4% utilization</span>. FP16 weights are causing excessive memory traffic on the N1 interconnect. KV cache is consuming 4.2 GB of working set.
            </p>

            {/* Badges */}
            <div className="flex flex-wrap gap-2 pt-1">
              <span className="px-2.5 py-1 rounded text-xs font-mono font-semibold bg-rose-500/15 text-rose-300 border border-rose-500/30">
                High Memory Pressure (92.4%)
              </span>
              <span className="px-2.5 py-1 rounded text-xs font-mono font-semibold bg-amber-500/15 text-amber-300 border border-amber-500/30">
                Suboptimal Thread Affinity (Unpinned)
              </span>
              <span className="px-2.5 py-1 rounded text-xs font-mono font-semibold bg-orange-500/15 text-orange-300 border border-orange-500/30">
                FP16 → INT4 Candidate (+169% TPS)
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* ── Configuration Comparison Cards (Side-by-Side) ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Left: Current Configuration */}
        <div className="rounded-xl bg-[#111827] border border-[#1F293D] p-5">
          <div className="flex items-center justify-between border-b border-[#1F293D] pb-3 mb-3">
            <h2 className="text-sm font-bold text-white tracking-wide">
              Current Configuration
            </h2>
            <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-zinc-800 text-zinc-400 border border-zinc-700">
              ACTIVE
            </span>
          </div>

          <div className="divide-y divide-[#1F293D]/60 text-xs font-mono space-y-2">
            <div className="pt-2 flex justify-between">
              <span className="text-zinc-400">Model</span>
              <span className="text-white">Llama-3.2-3B</span>
            </div>
            <div className="pt-2 flex justify-between">
              <span className="text-zinc-400">Quantization</span>
              <span className="text-zinc-300">FP16</span>
            </div>
            <div className="pt-2 flex justify-between">
              <span className="text-zinc-400">Batch Size</span>
              <span className="text-zinc-300">1</span>
            </div>
            <div className="pt-2 flex justify-between">
              <span className="text-zinc-400">Threads</span>
              <span className="text-zinc-300">8</span>
            </div>
            <div className="pt-2 flex justify-between">
              <span className="text-zinc-400">CPU Affinity</span>
              <span className="text-rose-400">Disabled</span>
            </div>
            <div className="pt-2 flex justify-between">
              <span className="text-zinc-400">KV Cache</span>
              <span className="text-zinc-300">Default (FP16)</span>
            </div>
            <div className="pt-2 flex justify-between">
              <span className="text-zinc-400">Runtime</span>
              <span className="text-zinc-300">llama.cpp v0.2</span>
            </div>
          </div>
        </div>

        {/* Right: Recommended Configuration */}
        <div className="rounded-xl bg-[#111827] border border-emerald-500/40 p-5 ring-1 ring-emerald-500/20">
          <div className="flex items-center justify-between border-b border-[#1F293D] pb-3 mb-3">
            <h2 className="text-sm font-bold text-white tracking-wide flex items-center gap-2">
              <SparklesIcon className="w-4 h-4 text-emerald-400" />
              Recommended Configuration
            </h2>
            <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
              +169% TPS
            </span>
          </div>

          <div className="divide-y divide-[#1F293D]/60 text-xs font-mono space-y-2">
            <div className="pt-2 flex justify-between">
              <span className="text-zinc-400">Model</span>
              <span className="text-white">Llama-3.2-3B</span>
            </div>
            <div className="pt-2 flex justify-between">
              <span className="text-zinc-400">Quantization</span>
              <span className="text-emerald-400 font-bold">INT4 (GGUF Q4_K_M)</span>
            </div>
            <div className="pt-2 flex justify-between">
              <span className="text-zinc-400">Batch Size</span>
              <span className="text-emerald-400 font-bold">8</span>
            </div>
            <div className="pt-2 flex justify-between">
              <span className="text-zinc-400">Threads</span>
              <span className="text-emerald-400 font-bold">32 (pinned)</span>
            </div>
            <div className="pt-2 flex justify-between">
              <span className="text-zinc-400">CPU Affinity</span>
              <span className="text-emerald-400 font-bold">NUMA-aware</span>
            </div>
            <div className="pt-2 flex justify-between">
              <span className="text-zinc-400">KV Cache</span>
              <span className="text-emerald-400 font-bold">Quantized Q8_0</span>
            </div>
            <div className="pt-2 flex justify-between">
              <span className="text-zinc-400">Runtime</span>
              <span className="text-emerald-400 font-bold">llama.cpp v0.3.8</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── Reasoning Cards (3 Rationale Cards) ── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="rounded-xl bg-[#111827] border border-[#1F293D] p-4">
          <div className="flex items-center gap-2 mb-2">
            <LayersIcon className="w-4 h-4 text-orange-400" />
            <h3 className="text-xs font-bold font-mono text-white">
              INT4 Quantization
            </h3>
          </div>
          <p className="text-xs text-zinc-300 leading-relaxed font-sans">
            Reduces working set memory traffic by <span className="text-emerald-400 font-bold">67%</span>, freeing up the N1 interconnect and eliminating memory stalls.
          </p>
        </div>

        <div className="rounded-xl bg-[#111827] border border-[#1F293D] p-4">
          <div className="flex items-center gap-2 mb-2">
            <CpuChipIcon className="w-4 h-4 text-orange-400" />
            <h3 className="text-xs font-bold font-mono text-white">
              Batch Size 8
            </h3>
          </div>
          <p className="text-xs text-zinc-300 leading-relaxed font-sans">
            Maximizes SVE2 vector compute efficiency across all 64 physical cores, unlocking <span className="text-emerald-400 font-bold">+3.1x</span> aggregate throughput.
          </p>
        </div>

        <div className="rounded-xl bg-[#111827] border border-[#1F293D] p-4">
          <div className="flex items-center gap-2 mb-2">
            <ZapIcon className="w-4 h-4 text-orange-400" />
            <h3 className="text-xs font-bold font-mono text-white">
              CPU Affinity Pinning
            </h3>
          </div>
          <p className="text-xs text-zinc-300 leading-relaxed font-sans">
            Pins threads to single L2 cache domains, eliminating cross-core thread migration latency and lowering TTFT by <span className="text-emerald-400 font-bold">15%</span>.
          </p>
        </div>
      </div>

      {/* ── Projected Changes Table ── */}
      <div className="rounded-xl bg-[#111827] border border-[#1F293D] overflow-hidden">
        <div className="p-4 border-b border-[#1F293D]">
          <h3 className="text-sm font-bold text-white tracking-wide">
            Projected Performance Deltas
          </h3>
          <p className="text-xs text-zinc-400 font-mono">
            Estimated performance change following recommended optimization
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-[#0E1422] text-zinc-400 border-b border-[#1F293D] uppercase text-[11px]">
              <tr>
                <th className="py-3 px-4 font-semibold">Metric</th>
                <th className="py-3 px-4 font-semibold">Current</th>
                <th className="py-3 px-4 font-semibold">Projected</th>
                <th className="py-3 px-4 font-semibold">Delta</th>
                <th className="py-3 px-4 font-semibold">Impact Assessment</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1F293D]/60 text-zinc-300">
              {[
                { metric: "TTFT", current: "127 ms", projected: "48 ms", delta: "↓ 62%", impact: "Significant latency drop" },
                { metric: "Tokens / Sec", current: "12.9", projected: "34.7", delta: "↑ 169%", impact: "2.7x generation speed" },
                { metric: "P95 Latency", current: "310 ms", projected: "104 ms", delta: "↓ 66%", impact: "Consistent SLA compliance" },
                { metric: "P99 Latency", current: "481 ms", projected: "162 ms", delta: "↓ 66%", impact: "Tail latency bounded" },
                { metric: "CPU Utilization", current: "91%", projected: "84%", delta: "↓ 7pp", impact: "Cores compute-bound" },
                { metric: "Memory Usage", current: "6.8 GB", projected: "3.2 GB", delta: "↓ 53%", impact: "Interconnect relieved" },
              ].map((row, i) => (
                <tr key={i} className="hover:bg-[#162032] transition-colors">
                  <td className="py-3 px-4 font-bold text-white">{row.metric}</td>
                  <td className="py-3 px-4 text-zinc-400">{row.current}</td>
                  <td className="py-3 px-4 font-semibold text-emerald-400">{row.projected}</td>
                  <td className="py-3 px-4 font-bold text-emerald-400">{row.delta}</td>
                  <td className="py-3 px-4 text-zinc-400 font-sans text-xs">{row.impact}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── JSON Export Modal ── */}
      {jsonModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-xl bg-[#111827] border border-[#1F293D] shadow-2xl p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-[#1F293D] pb-3">
              <h3 className="text-sm font-bold text-white font-mono flex items-center gap-2">
                <DownloadIcon className="w-4 h-4 text-orange-400" />
                Exported Configuration JSON
              </h3>
              <button
                onClick={() => setJsonModalOpen(false)}
                className="text-zinc-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="rounded-lg bg-[#0B0F19] border border-[#1F293D] p-3 text-xs font-mono text-emerald-400 overflow-x-auto max-h-64">
              <pre>{JSON.stringify(recommendedJson, null, 2)}</pre>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setJsonModalOpen(false)}
                className="px-3 py-1.5 rounded bg-zinc-800 text-xs font-mono text-zinc-300 hover:bg-zinc-700"
              >
                Close
              </button>
              <button
                onClick={handleCopyJson}
                className="px-4 py-1.5 rounded bg-[#EA580C] hover:bg-[#FF7315] text-xs font-mono text-white font-bold flex items-center gap-1.5"
              >
                {copied ? <CheckIcon className="w-3.5 h-3.5" /> : <CopyIcon className="w-3.5 h-3.5" />}
                {copied ? "Copied!" : "Copy JSON"}
              </button>
            </div>
          </div>
        </div>
      )}
    </AppLayout>
  );
}
