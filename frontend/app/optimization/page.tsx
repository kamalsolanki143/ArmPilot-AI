"use client";

import React, { useState } from "react";
import AppLayout from "@/components/AppLayout";
import { apiService } from "@/services/api";
import {
  SlidersIcon,
  ZapIcon,
  CheckIcon,
  RefreshIcon,
  CpuChipIcon,
  LayersIcon,
} from "@/components/Icons";

export default function OptimizationPage() {
  const [quantization, setQuantization] = useState<"FP32" | "BF16" | "FP16" | "INT8" | "INT4">("INT4");
  const [batchSize, setBatchSize] = useState(8);
  const [threadCount, setThreadCount] = useState(32);

  // Arm toggles
  const [cpuAffinity, setCpuAffinity] = useState(true);
  const [kvCacheOpt, setKvCacheOpt] = useState(true);
  const [numaAware, setNumaAware] = useState(false);
  const [runtime, setRuntime] = useState("llama.cpp");

  const [isOptimizing, setIsOptimizing] = useState(false);
  const [optSuccess, setOptSuccess] = useState(false);

  // Descriptions for quantization
  const quantDescriptions: Record<string, string> = {
    FP32: "Full 32-bit floating point precision. Maximum memory footprint (~14.8 GB for 7B) with no compression or quantization speedup.",
    BF16: "Brain Floating Point 16-bit. Preserves dynamic range with 50% memory reduction vs FP32. Supported natively on Armv8.6-A.",
    FP16: "Standard IEEE half-precision. 50% memory reduction with native Arm NEON vector acceleration.",
    INT8: "8-bit integer quantization using GGUF Q8_0. ~60% memory savings and 2.1x throughput boost on Neoverse N1 DotProd instructions.",
    INT4: "4-bit integer weights using GGUF Q4_K_M. Yields up to 67% memory reduction and +169% throughput with <1% perplexity delta on SVE2.",
  };

  // Dynamic impact estimation based on current controls
  const calculateImpact = () => {
    let mem = "-53%";
    let tps = "+169%";
    let ttft = "-62%";
    let loss = "<1%";

    if (quantization === "FP32") {
      mem = "0%";
      tps = "0%";
      ttft = "0%";
      loss = "0%";
    } else if (quantization === "FP16") {
      mem = "-50%";
      tps = "+42%";
      ttft = "-25%";
      loss = "<0.1%";
    } else if (quantization === "INT8") {
      mem = "-60%";
      tps = "+112%";
      ttft = "-45%";
      loss = "<0.4%";
    } else if (quantization === "INT4") {
      mem = "-67%";
      tps = `+${140 + batchSize * 4}%`;
      ttft = "-62%";
      loss = "<0.8%";
    }

    return { mem, tps, ttft, loss };
  };

  const impact = calculateImpact();

  const handleRunOptimization = async () => {
    setIsOptimizing(true);
    setOptSuccess(false);

    try {
      await apiService.runOptimization({
        model: "Llama-3.2-3B",
        quantization,
        batchSize,
        threadCount,
        cpuAffinity,
        kvCacheOpt,
        numaAware,
        runtime,
      });

      setTimeout(() => {
        setIsOptimizing(false);
        setOptSuccess(true);
        setTimeout(() => setOptSuccess(false), 4000);
      }, 1200);
    } catch {
      setIsOptimizing(false);
    }
  };

  return (
    <AppLayout pageTitle="Optimization Engine">
      {/* ── Header ── */}
      <div className="pb-2 border-b border-[#1F293D]/60">
        <h1 className="text-2xl font-bold tracking-tight text-white">
          Optimization Engine
        </h1>
        <p className="text-xs sm:text-sm text-zinc-400 font-mono mt-1">
          Tune quantization, threading, memory, and Arm-specific hardware parameters
        </p>
      </div>

      {/* ── 2x2 Grid of Optimization Controls ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Top Left: Quantization */}
        <div className="rounded-xl bg-[#111827] border border-[#1F293D] p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-bold text-white tracking-wide flex items-center gap-2">
                <LayersIcon className="w-4 h-4 text-orange-400" />
                Quantization
              </h2>
              <span className="text-xs font-mono text-zinc-400">Arm DotProd / SVE2</span>
            </div>

            {/* 5 Quantization Buttons */}
            <div className="grid grid-cols-5 gap-2 mb-4">
              {(["FP32", "BF16", "FP16", "INT8", "INT4"] as const).map((q) => (
                <button
                  key={q}
                  onClick={() => setQuantization(q)}
                  className={`py-2.5 rounded-lg text-xs font-mono font-bold transition-all cursor-pointer ${
                    quantization === q
                      ? "bg-[#EA580C] text-white shadow-md shadow-orange-600/30 ring-1 ring-orange-400"
                      : "bg-[#0B0F19] text-zinc-300 border border-[#1F293D] hover:bg-[#162032] hover:text-white"
                  }`}
                >
                  {q}
                </button>
              ))}
            </div>

            {/* Dynamic Description Box */}
            <div className="rounded-lg bg-[#0B0F19] border border-[#1F293D] p-3.5 text-xs text-zinc-300 font-sans leading-relaxed">
              <span className="font-bold text-white font-mono block mb-1">
                {quantization} Configuration:
              </span>
              {quantDescriptions[quantization]}
            </div>
          </div>
        </div>

        {/* Top Right: Compute Configuration */}
        <div className="rounded-xl bg-[#111827] border border-[#1F293D] p-5 space-y-5">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-white tracking-wide flex items-center gap-2">
              <CpuChipIcon className="w-4 h-4 text-orange-400" />
              Compute Configuration
            </h2>
            <span className="text-xs font-mono text-zinc-400">Neoverse N1 (64 Cores)</span>
          </div>

          {/* Batch Size Slider */}
          <div>
            <div className="flex justify-between text-xs font-mono mb-2">
              <span className="text-zinc-400 font-semibold">Batch Size</span>
              <span className="text-white font-bold">{batchSize}</span>
            </div>
            <input
              type="range"
              min="1"
              max="64"
              step="1"
              value={batchSize}
              onChange={(e) => setBatchSize(Number(e.target.value))}
              className="w-full cursor-pointer h-2 bg-[#0B0F19] rounded-lg appearance-none"
            />
            <div className="flex justify-between text-[10px] font-mono text-zinc-400 mt-1">
              <span>1 (Single Stream)</span>
              <span>16</span>
              <span>32</span>
              <span>64 (High Throughput)</span>
            </div>
          </div>

          {/* Thread Count Slider */}
          <div>
            <div className="flex justify-between text-xs font-mono mb-2">
              <span className="text-zinc-400 font-semibold">Thread Count</span>
              <span className="text-white font-bold">{threadCount} threads</span>
            </div>
            <input
              type="range"
              min="1"
              max="64"
              step="1"
              value={threadCount}
              onChange={(e) => setThreadCount(Number(e.target.value))}
              className="w-full cursor-pointer h-2 bg-[#0B0F19] rounded-lg appearance-none"
            />
            <div className="flex justify-between text-[10px] font-mono text-zinc-400 mt-1">
              <span>1</span>
              <span>16</span>
              <span>32 (Optimal)</span>
              <span>64 (Max)</span>
            </div>
          </div>
        </div>

        {/* Bottom Left: Arm-Specific Optimizations */}
        <div className="rounded-xl bg-[#111827] border border-[#1F293D] p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-white tracking-wide flex items-center gap-2">
              <ZapIcon className="w-4 h-4 text-orange-400" />
              Arm-Specific Optimizations
            </h2>
            <span className="text-xs font-mono text-emerald-400">aarch64</span>
          </div>

          {/* 3 Toggles */}
          <div className="space-y-3">
            {[
              {
                id: "affinity",
                title: "CPU Affinity Pinning",
                desc: "Pins inference threads to physical L2 cache core domains",
                checked: cpuAffinity,
                setter: setCpuAffinity,
              },
              {
                id: "kv",
                title: "KV Cache Optimization",
                desc: "Quantizes intermediate key-value attention tensors to Q8_0",
                checked: kvCacheOpt,
                setter: setKvCacheOpt,
              },
              {
                id: "numa",
                title: "NUMA-Aware Scheduling",
                desc: "Interleaves memory allocations across multi-socket domains",
                checked: numaAware,
                setter: setNumaAware,
              },
            ].map((t) => (
              <div
                key={t.id}
                className="flex items-center justify-between p-2.5 rounded-lg bg-[#0B0F19] border border-[#1F293D]"
              >
                <div>
                  <div className="text-xs font-bold text-white font-mono">{t.title}</div>
                  <div className="text-[11px] text-zinc-400">{t.desc}</div>
                </div>

                <button
                  type="button"
                  onClick={() => t.setter(!t.checked)}
                  className={`w-10 h-5 flex items-center rounded-full p-0.5 transition-colors cursor-pointer ${
                    t.checked ? "bg-[#EA580C]" : "bg-zinc-700"
                  }`}
                >
                  <div
                    className={`bg-white w-4 h-4 rounded-full shadow-md transform transition-transform ${
                      t.checked ? "translate-x-5" : "translate-x-0"
                    }`}
                  />
                </button>
              </div>
            ))}
          </div>

          {/* Selectable Runtime Engine Buttons */}
          <div>
            <label className="block text-xs font-mono text-zinc-400 uppercase tracking-wider mb-2 font-semibold">
              Inference Runtime
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {["llama.cpp", "ExecuTorch", "ONNX Runtime", "TensorRT-LLM"].map((rt) => (
                <button
                  key={rt}
                  onClick={() => setRuntime(rt)}
                  className={`py-2 px-2 rounded-lg text-xs font-mono text-center font-medium transition-all ${
                    runtime === rt
                      ? "bg-[#1E293B] border-orange-500 text-white font-bold border ring-1 ring-orange-500"
                      : "bg-[#0B0F19] border border-[#1F293D] text-zinc-400 hover:text-zinc-200"
                  }`}
                >
                  {rt}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Bottom Right: Estimated Impact */}
        <div className="rounded-xl bg-[#111827] border border-[#1F293D] p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-bold text-white tracking-wide">
                Estimated Impact
              </h2>
              <span className="text-xs font-mono text-zinc-400">vs FP16 Baseline</span>
            </div>

            {/* Impact Metric Grid */}
            <div className="grid grid-cols-2 gap-3 mb-4">
              <div className="p-3 rounded-lg bg-[#0B0F19] border border-cyan-500/20 text-center">
                <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-400 block mb-1">
                  Memory Reduction
                </span>
                <span className="text-xl font-bold font-mono text-cyan-400">
                  {impact.mem}
                </span>
              </div>

              <div className="p-3 rounded-lg bg-[#0B0F19] border border-emerald-500/20 text-center">
                <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-400 block mb-1">
                  Throughput Gain
                </span>
                <span className="text-xl font-bold font-mono text-emerald-400">
                  {impact.tps}
                </span>
              </div>

              <div className="p-3 rounded-lg bg-[#0B0F19] border border-emerald-500/20 text-center">
                <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-400 block mb-1">
                  TTFT Improvement
                </span>
                <span className="text-xl font-bold font-mono text-emerald-400">
                  {impact.ttft}
                </span>
              </div>

              <div className="p-3 rounded-lg bg-[#0B0F19] border border-orange-500/20 text-center">
                <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-400 block mb-1">
                  Perplexity Delta
                </span>
                <span className="text-xl font-bold font-mono text-orange-400">
                  {impact.loss}
                </span>
              </div>
            </div>
          </div>

          <div>
            {optSuccess && (
              <div className="mb-3 p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-mono flex items-center gap-2">
                <CheckIcon className="w-4 h-4" />
                <span>Optimization profile generated & saved as candidate OPT-942</span>
              </div>
            )}

            <button
              onClick={handleRunOptimization}
              disabled={isOptimizing}
              className="w-full py-3 rounded-lg bg-[#EA580C] hover:bg-[#FF7315] disabled:opacity-75 text-white font-bold text-sm shadow-lg shadow-orange-600/25 flex items-center justify-center gap-2 transition-all hover:scale-[1.01] cursor-pointer"
            >
              {isOptimizing ? (
                <>
                  <RefreshIcon className="w-4 h-4 animate-spin" />
                  <span>Evaluating Parameters...</span>
                </>
              ) : (
                <>
                  <ZapIcon className="w-4 h-4" />
                  <span>⚡ Run Optimization</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
