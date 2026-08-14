"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  LogoIcon,
  CpuChipIcon,
  GaugeIcon,
  SlidersIcon,
  SparklesIcon,
  TerminalIcon,
  LayersIcon,
  ActivityIcon,
  ZapIcon,
  CheckIcon,
  ArrowRightIcon,
  ArrowUpRightIcon,
  ShieldCheckIcon,
  FileTextIcon,
  HistoryIcon,
} from "@/components/Icons";

export default function LandingPage() {
  const [activeWorkflowStep, setActiveWorkflowStep] = useState(0);
  const [activePreviewTab, setActivePreviewTab] = useState<"overview" | "benchmark" | "recommendations">("overview");

  const workflowSteps = [
    {
      num: "01",
      title: "Select Model",
      desc: "Choose from optimized open-source LLMs including Llama 3.2, Mistral 7B, Phi-3 Mini, Gemma 2B, and Qwen2.5.",
      badge: "GGUF / Safetensors",
    },
    {
      num: "02",
      title: "Configure Runtime",
      desc: "Tune concurrency, thread affinity pinning, KV cache quantization, batch size, and execution backends (llama.cpp, ExecuTorch).",
      badge: "Arm SVE2 / NEON",
    },
    {
      num: "03",
      title: "Run Benchmark",
      desc: "Execute automated micro-benchmarks with high-resolution telemetry capturing TTFT, P95/P99 latency, and interconnect load.",
      badge: "Sub-millisecond Precision",
    },
    {
      num: "04",
      title: "Analyze & Optimize",
      desc: "Diagnose memory bandwidth bottlenecks with automated AI recommendations and export reproducible benchmark reports.",
      badge: "+169% Throughput Gain",
    },
  ];

  return (
    <div className="min-h-screen bg-[#0B0F19] text-[#F3F4F6] selection:bg-orange-500/30 selection:text-white flex flex-col font-sans overflow-x-hidden">
      {/* ── Top Navigation Bar ── */}
      <header className="sticky top-0 z-50 w-full border-b border-[#1F293D]/80 bg-[#0B0F19]/90 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3 group">
            <LogoIcon className="w-8 h-8 rounded-lg shadow-md shadow-orange-500/20 group-hover:scale-105 transition-transform" />
            <div>
              <span className="text-lg font-bold tracking-tight text-white flex items-center gap-1.5">
                ArmPilot
                <span className="text-xs font-semibold px-1.5 py-0.5 rounded bg-orange-500/15 text-orange-400 border border-orange-500/30">
                  AI
                </span>
              </span>
            </div>
          </Link>

          <nav className="hidden md:flex items-center gap-8 text-xs font-mono">
            <a href="#features" className="text-zinc-300 hover:text-white transition-colors">
              Features
            </a>
            <a href="#workflow" className="text-zinc-300 hover:text-white transition-colors">
              Workflow
            </a>
            <a href="#metrics" className="text-zinc-300 hover:text-white transition-colors">
              Telemetry
            </a>
            <a href="#arm64" className="text-zinc-300 hover:text-white transition-colors">
              Why ARM64
            </a>
            <a href="#preview" className="text-zinc-300 hover:text-white transition-colors">
              Platform Preview
            </a>
          </nav>

          <div className="flex items-center gap-3">
            <Link
              href="/dashboard"
              className="px-4 py-2 rounded-lg bg-[#EA580C] hover:bg-[#FF7315] text-white text-xs sm:text-sm font-semibold shadow-lg shadow-orange-600/25 flex items-center gap-2 transition-all hover:scale-[1.02] cursor-pointer"
            >
              <span>Launch App</span>
              <ArrowRightIcon className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </header>

      {/* ── HERO SECTION ── */}
      <section className="relative pt-16 pb-20 md:pt-24 md:pb-28 overflow-hidden border-b border-[#1F293D]/60">
        {/* Subtle developer grid background */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#1F293D15_1px,transparent_1px),linear-gradient(to_bottom,#1F293D15_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] pointer-events-none" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
            {/* Hero Left Column (7 cols) */}
            <div className="lg:col-span-7 space-y-6 text-left">
              {/* Product Badge */}
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#162032] border border-[#1F293D] text-xs font-mono text-zinc-300">
                <CpuChipIcon className="w-3.5 h-3.5 text-orange-400" />
                <span>Arm64-First LLM Optimization & Benchmarking Platform</span>
              </div>

              {/* Headline */}
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white leading-[1.1]">
                Optimize LLM Inference for <span className="text-[#EA580C]">ARM64</span>
              </h1>

              {/* Supporting Text */}
              <p className="text-base sm:text-lg text-zinc-300 max-w-2xl leading-relaxed font-sans">
                Deploy, benchmark, optimize, and compare open-source LLMs on ARM64 infrastructure. Unlock up to <strong>+169% throughput</strong> with SVE2 vector acceleration, NUMA thread pinning, and INT4 quantization.
              </p>

              {/* CTAs */}
              <div className="pt-2 flex flex-col sm:flex-row items-stretch sm:items-center gap-3.5">
                <Link
                  href="/dashboard"
                  className="px-6 py-3.5 rounded-lg bg-[#EA580C] hover:bg-[#FF7315] text-white text-sm font-bold shadow-xl shadow-orange-600/25 flex items-center justify-center gap-2.5 transition-all hover:scale-[1.02] cursor-pointer"
                >
                  <ZapIcon className="w-4 h-4" />
                  <span>Launch ArmPilot-AI</span>
                </Link>

                <a
                  href="#features"
                  className="px-5 py-3.5 rounded-lg bg-[#111827] hover:bg-[#162032] text-zinc-200 hover:text-white text-sm font-medium border border-[#1F293D] flex items-center justify-center gap-2 transition-colors"
                >
                  <span>Explore Features</span>
                  <ArrowRightIcon className="w-3.5 h-3.5 text-zinc-400" />
                </a>
              </div>

              {/* Quick Specs Snippet */}
              <div className="pt-4 flex flex-wrap items-center gap-x-6 gap-y-2 text-xs font-mono text-zinc-400 border-t border-[#1F293D]/60">
                <span className="flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                  Arm Neoverse N1 / V2
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
                  SVE2 & NEON Vectors
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-orange-400" />
                  llama.cpp & GGUF
                </span>
              </div>
            </div>

            {/* Hero Right Column: Interactive ARM64 Compute Telemetry Visualizer (5 cols) */}
            <div className="lg:col-span-5">
              <div className="rounded-2xl bg-[#111827] border border-[#1F293D] shadow-2xl p-5 relative overflow-hidden">
                {/* Visualizer Header */}
                <div className="flex items-center justify-between border-b border-[#1F293D] pb-3 mb-4">
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full bg-rose-500/80 inline-block" />
                    <span className="w-3 h-3 rounded-full bg-amber-500/80 inline-block" />
                    <span className="w-3 h-3 rounded-full bg-emerald-500/80 inline-block" />
                    <span className="text-xs font-mono text-zinc-400 ml-2">arm64-telemetry.log</span>
                  </div>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 font-bold">
                    LIVE STREAM
                  </span>
                </div>

                {/* Model Telemetry Panel */}
                <div className="space-y-3 font-mono text-xs">
                  <div className="p-3 rounded-lg bg-[#0B0F19] border border-[#1F293D]">
                    <div className="flex justify-between text-zinc-400 mb-1">
                      <span>TARGET HARDWARE</span>
                      <span className="text-white font-bold">Neoverse N1 (64c)</span>
                    </div>
                    <div className="flex justify-between text-zinc-400">
                      <span>ACTIVE MODEL</span>
                      <span className="text-orange-400 font-bold">Llama-3.2-3B INT4</span>
                    </div>
                  </div>

                  {/* 3 Metric Chips */}
                  <div className="grid grid-cols-3 gap-2 text-center">
                    <div className="p-2.5 rounded-lg bg-[#0B0F19] border border-cyan-500/30">
                      <span className="text-[10px] text-zinc-400 block uppercase">TTFT</span>
                      <span className="text-base font-bold text-cyan-400 font-mono">48 ms</span>
                      <span className="text-[9px] text-emerald-400 block">-62%</span>
                    </div>

                    <div className="p-2.5 rounded-lg bg-[#0B0F19] border border-emerald-500/30">
                      <span className="text-[10px] text-zinc-400 block uppercase">VELOCITY</span>
                      <span className="text-base font-bold text-emerald-400 font-mono">34.7 tps</span>
                      <span className="text-[9px] text-emerald-400 block">+169%</span>
                    </div>

                    <div className="p-2.5 rounded-lg bg-[#0B0F19] border border-orange-500/30">
                      <span className="text-[10px] text-zinc-400 block uppercase">P95 LAT</span>
                      <span className="text-base font-bold text-orange-400 font-mono">104 ms</span>
                      <span className="text-[9px] text-emerald-400 block">-66%</span>
                    </div>
                  </div>

                  {/* Terminal Execution Snippet */}
                  <div className="p-3 rounded-lg bg-[#0B0F19] border border-[#1F293D] text-[11px] text-zinc-300 space-y-1">
                    <p className="text-zinc-500">$ armpilot benchmark --model llama-3.2-3b --threads 32</p>
                    <p className="text-emerald-400">✓ Detected 64 aarch64 cores with SVE2 vector support</p>
                    <p className="text-cyan-400">✓ KV cache compressed: Q8_0 page table (3.2 GB total)</p>
                    <p className="text-orange-400">✓ Peak throughput reached: 2,840 tokens/min (+2.7×)</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── 2. TRUST / VALUE STRIP ── */}
      <section className="py-6 border-b border-[#1F293D] bg-[#0E1422]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4 text-center">
            {[
              { label: "ARM64 First", sub: "Native vector acceleration" },
              { label: "LLM Benchmarking", sub: "Sub-ms latency telemetry" },
              { label: "Inference Optimization", sub: "INT4/INT8 quantization" },
              { label: "Open Source Models", sub: "Llama, Mistral, Phi-3, Gemma" },
              { label: "Real-Time Performance", sub: "Micro-profiling & bottlenecks" },
            ].map((item, idx) => (
              <div key={idx} className="p-2.5">
                <div className="text-xs sm:text-sm font-bold text-white font-mono flex items-center justify-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#EA580C]" />
                  {item.label}
                </div>
                <div className="text-[11px] text-zinc-400 mt-0.5">{item.sub}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── 3. PROBLEM SECTION ── */}
      <section className="py-20 border-b border-[#1F293D]/60 relative">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl mx-auto text-center space-y-4 mb-12">
            <span className="text-xs font-mono uppercase tracking-wider text-orange-400 font-semibold">
              The ARM64 Challenge
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
              Running LLMs efficiently on ARM64 is not as simple as picking a model.
            </h2>
            <p className="text-zinc-300 text-sm sm:text-base leading-relaxed font-sans">
              Deploying large models on CPU-efficient ARM architectures requires balancing complex hardware interconnects, memory bandwidth saturation, thread affinity, and quantization trade-offs.
            </p>
          </div>

          {/* 7 Engineering Dimensions Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-7 gap-3 text-center">
            {[
              { title: "Latency", desc: "P50, P95 & P99 bounds" },
              { title: "Throughput", desc: "Tokens per second rate" },
              { title: "Memory Bandwidth", desc: "Interconnect saturation" },
              { title: "TTFT", desc: "Time to first token" },
              { title: "Runtime Config", desc: "Thread & cache affinity" },
              { title: "Model Format", desc: "GGUF quantization" },
              { title: "CPU Utilization", desc: "64-core compute balance" },
            ].map((p, idx) => (
              <div
                key={idx}
                className="p-3.5 rounded-xl bg-[#111827] border border-[#1F293D] hover:border-orange-500/40 transition-colors"
              >
                <div className="text-xs font-bold text-white font-mono">{p.title}</div>
                <div className="text-[11px] text-zinc-400 mt-1 font-sans">{p.desc}</div>
              </div>
            ))}
          </div>

          <div className="mt-8 text-center">
            <div className="inline-block p-3 rounded-xl bg-orange-500/10 border border-orange-500/30 text-xs sm:text-sm font-mono text-orange-300">
              ⚡ ArmPilot-AI brings these measurements and automated optimization workflows into one unified platform.
            </div>
          </div>
        </div>
      </section>

      {/* ── 4. SOLUTION SECTION (4 Feature Cards) ── */}
      <section id="features" className="py-20 border-b border-[#1F293D]/60 bg-[#0E1422]/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center space-y-3 mb-14">
            <span className="text-xs font-mono uppercase tracking-wider text-orange-400 font-semibold">
              Core Capabilities
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
              A Complete Platform for Arm-Accelerated LLMs
            </h2>
            <p className="text-zinc-400 text-sm max-w-xl mx-auto">
              Engineered specifically for Neoverse, Graviton, Ampere, and Apple Silicon compute environments.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Feature 1: Deploy */}
            <div className="rounded-xl bg-[#111827] border border-[#1F293D] hover:border-orange-500/50 p-6 flex flex-col justify-between transition-all hover:-translate-y-1">
              <div>
                <div className="w-10 h-10 rounded-lg bg-orange-500/15 border border-orange-500/30 text-orange-400 flex items-center justify-center mb-4">
                  <TerminalIcon className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-white mb-2">Deploy</h3>
                <p className="text-xs sm:text-sm text-zinc-300 leading-relaxed font-sans">
                  Run supported open-source models (Llama 3.2, Mistral 7B, Phi-3, Gemma, Qwen2.5) directly on ARM64 infrastructure with native SVE2 & NEON execution.
                </p>
              </div>
              <div className="pt-4 text-xs font-mono text-orange-400 flex items-center gap-1">
                <span>Multi-model runtime</span>
                <ArrowRightIcon className="w-3 h-3" />
              </div>
            </div>

            {/* Feature 2: Benchmark */}
            <div className="rounded-xl bg-[#111827] border border-[#1F293D] hover:border-cyan-500/50 p-6 flex flex-col justify-between transition-all hover:-translate-y-1">
              <div>
                <div className="w-10 h-10 rounded-lg bg-cyan-500/15 border border-cyan-500/30 text-cyan-400 flex items-center justify-center mb-4">
                  <GaugeIcon className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-white mb-2">Benchmark</h3>
                <p className="text-xs sm:text-sm text-zinc-300 leading-relaxed font-sans">
                  Measure latency percentiles (P50/P95/P99), throughput, TTFT, tokens/sec, working set memory footprint, and physical core utilization curves.
                </p>
              </div>
              <div className="pt-4 text-xs font-mono text-cyan-400 flex items-center gap-1">
                <span>High-resolution telemetry</span>
                <ArrowRightIcon className="w-3 h-3" />
              </div>
            </div>

            {/* Feature 3: Optimize */}
            <div className="rounded-xl bg-[#111827] border border-[#1F293D] hover:border-emerald-500/50 p-6 flex flex-col justify-between transition-all hover:-translate-y-1">
              <div>
                <div className="w-10 h-10 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 flex items-center justify-center mb-4">
                  <SlidersIcon className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-white mb-2">Optimize</h3>
                <p className="text-xs sm:text-sm text-zinc-300 leading-relaxed font-sans">
                  Experiment with runtime parameters, INT4/INT8 quantization, thread affinity pinning, NUMA-aware memory interleaving, and KV cache compression.
                </p>
              </div>
              <div className="pt-4 text-xs font-mono text-emerald-400 flex items-center gap-1">
                <span>Auto parameter tuning</span>
                <ArrowRightIcon className="w-3 h-3" />
              </div>
            </div>

            {/* Feature 4: Compare */}
            <div className="rounded-xl bg-[#111827] border border-[#1F293D] hover:border-purple-500/50 p-6 flex flex-col justify-between transition-all hover:-translate-y-1">
              <div>
                <div className="w-10 h-10 rounded-lg bg-purple-500/15 border border-purple-500/30 text-purple-400 flex items-center justify-center mb-4">
                  <LayersIcon className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-white mb-2">Compare</h3>
                <p className="text-xs sm:text-sm text-zinc-300 leading-relaxed font-sans">
                  Evaluate models and configuration combinations side-by-side using reproducible data, before/after charts, and exportable executive reports.
                </p>
              </div>
              <div className="pt-4 text-xs font-mono text-purple-400 flex items-center gap-1">
                <span>Side-by-side diffs</span>
                <ArrowRightIcon className="w-3 h-3" />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── 5. HOW IT WORKS (4-Step Workflow) ── */}
      <section id="workflow" className="py-20 border-b border-[#1F293D]/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center space-y-3 mb-14">
            <span className="text-xs font-mono uppercase tracking-wider text-orange-400 font-semibold">
              Workflow Pipeline
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
              How ArmPilot-AI Works
            </h2>
            <p className="text-zinc-400 text-sm max-w-xl mx-auto">
              From model selection to hardware-optimized production inference in four simple stages.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 relative">
            {workflowSteps.map((step, idx) => (
              <div
                key={idx}
                onClick={() => setActiveWorkflowStep(idx)}
                className={`rounded-xl p-5 border cursor-pointer transition-all duration-200 ${
                  activeWorkflowStep === idx
                    ? "bg-[#162032] border-orange-500 ring-1 ring-orange-500/40"
                    : "bg-[#111827] border-[#1F293D] hover:bg-[#141C2E]"
                }`}
              >
                <div className="flex items-center justify-between mb-3">
                  <span className="text-2xl font-bold font-mono text-orange-400">
                    {step.num}
                  </span>
                  <span className="text-[10px] px-2 py-0.5 rounded font-mono bg-[#0B0F19] text-zinc-300 border border-[#1F293D]">
                    {step.badge}
                  </span>
                </div>
                <h3 className="text-sm font-bold text-white mb-2">{step.title}</h3>
                <p className="text-xs text-zinc-300 leading-relaxed font-sans">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── 6. KEY METRICS SECTION ── */}
      <section id="metrics" className="py-20 border-b border-[#1F293D]/60 bg-[#0E1422]/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center space-y-3 mb-14">
            <span className="text-xs font-mono uppercase tracking-wider text-orange-400 font-semibold">
              Telemetry Readout
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
              Real-World Neoverse N1 Benchmark Metrics
            </h2>
            <p className="text-zinc-400 text-sm max-w-xl mx-auto">
              Live measurements collected on 64-core Arm architecture running Llama 3.2 3B INT4.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[
              {
                title: "Tokens / Second",
                val: "34.7",
                unit: "tps",
                delta: "+169% vs baseline",
                color: "text-emerald-400",
                desc: "Generation velocity achieved through 32 pinned threads & SVE2.",
              },
              {
                title: "Time to First Token (TTFT)",
                val: "48",
                unit: "ms",
                delta: "-62% vs baseline",
                color: "text-cyan-400",
                desc: "Prompt prefill latency reduced via quantized KV cache allocation.",
              },
              {
                title: "P95 Latency",
                val: "104",
                unit: "ms",
                delta: "-66% vs baseline",
                color: "text-orange-400",
                desc: "95th percentile request completion time under concurrent load.",
              },
              {
                title: "Working Set Memory",
                val: "3.2",
                unit: "GB",
                delta: "-53% memory reduction",
                color: "text-cyan-400",
                desc: "Total RAM footprint with INT4 GGUF weights + dynamic context buffer.",
              },
              {
                title: "Aggregate Throughput",
                val: "2,840",
                unit: "tok/min",
                delta: "+2.7× speedup",
                color: "text-purple-400",
                desc: "Sustained batch throughput across 16 concurrent requests.",
              },
              {
                title: "CPU Utilization",
                val: "84%",
                unit: "",
                delta: "64 cores balanced",
                color: "text-zinc-200",
                desc: "High compute saturation without thermal or interconnect throttling.",
              },
            ].map((m, idx) => (
              <div
                key={idx}
                className="rounded-xl bg-[#111827] border border-[#1F293D] p-5 space-y-2 hover:border-zinc-500 transition-colors"
              >
                <div className="text-xs font-mono uppercase tracking-wider text-zinc-400 font-semibold">
                  {m.title}
                </div>
                <div className="flex items-baseline gap-1.5">
                  <span className={`text-3xl font-bold font-mono ${m.color}`}>
                    {m.val}
                  </span>
                  {m.unit && <span className="text-xs font-mono text-zinc-400">{m.unit}</span>}
                </div>
                <div className="text-xs font-mono text-emerald-400 font-semibold">{m.delta}</div>
                <p className="text-xs text-zinc-400 font-sans pt-1 border-t border-[#1F293D]/60">{m.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── 7. ARM64 FOCUS SECTION ── */}
      <section id="arm64" className="py-20 border-b border-[#1F293D]/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
            <div className="lg:col-span-6 space-y-5">
              <span className="text-xs font-mono uppercase tracking-wider text-orange-400 font-semibold">
                Architecture Advantage
              </span>
              <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
                Why ARM64 is the Future of CPU-Efficient Inference
              </h2>
              <p className="text-zinc-300 text-sm sm:text-base leading-relaxed font-sans">
                As LLMs become smaller and more specialized, running cost-effective inference on ARM64 infrastructure provides distinct architectural advantages over traditional power-hungry GPU clusters.
              </p>

              <div className="space-y-3 pt-2">
                {[
                  {
                    title: "Lower Power Consumption & TCO",
                    desc: "Up to 3x higher performance-per-watt on cloud instances (AWS Graviton, Ampere Altra) reduces monthly inference compute bills.",
                  },
                  {
                    title: "High Core-Density Scaling",
                    desc: "64 to 128 physical Neoverse cores per socket allow massive concurrency without multi-GPU interconnect bottlenecks.",
                  },
                  {
                    title: "Unified Edge & Server Deployments",
                    desc: "Run identical quantized model pipelines across edge devices, developer laptops (Apple Silicon), and enterprise servers.",
                  },
                  {
                    title: "Hardware Vector Extensions",
                    desc: "Arm Scalable Vector Extension 2 (SVE2) and Dot Product instructions accelerate int4/int8 matrix ops natively in hardware.",
                  },
                ].map((item, idx) => (
                  <div key={idx} className="flex items-start gap-3">
                    <div className="w-5 h-5 rounded-full bg-orange-500/20 text-orange-400 flex items-center justify-center mt-0.5 shrink-0">
                      <CheckIcon className="w-3 h-3" />
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-white font-mono">{item.title}</h4>
                      <p className="text-xs text-zinc-400 font-sans mt-0.5">{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Right Side Visual Specs Table */}
            <div className="lg:col-span-6">
              <div className="rounded-2xl bg-[#111827] border border-[#1F293D] p-6 space-y-4 shadow-xl">
                <div className="flex items-center justify-between border-b border-[#1F293D] pb-3">
                  <h3 className="text-sm font-bold text-white font-mono">
                    Arm Architecture Compatibility Matrix
                  </h3>
                  <span className="text-xs font-mono text-emerald-400">100% Tested</span>
                </div>

                <div className="divide-y divide-[#1F293D]/60 text-xs font-mono">
                  <div className="py-2.5 flex justify-between">
                    <span className="text-zinc-400">AWS Graviton3 / Graviton4</span>
                    <span className="text-emerald-400 font-bold">Optimized (SVE2)</span>
                  </div>
                  <div className="py-2.5 flex justify-between">
                    <span className="text-zinc-400">Ampere Altra / Altra Max</span>
                    <span className="text-emerald-400 font-bold">Optimized (NEON DotProd)</span>
                  </div>
                  <div className="py-2.5 flex justify-between">
                    <span className="text-zinc-400">Apple Silicon (M-Series)</span>
                    <span className="text-emerald-400 font-bold">Optimized (NEON + AMX)</span>
                  </div>
                  <div className="py-2.5 flex justify-between">
                    <span className="text-zinc-400">Raspberry Pi 5 / RK3588 (Edge)</span>
                    <span className="text-emerald-400 font-bold">Optimized (GGUF Q4)</span>
                  </div>
                  <div className="py-2.5 flex justify-between">
                    <span className="text-zinc-400">Oracle Ampere A1 Compute</span>
                    <span className="text-emerald-400 font-bold">Optimized (NUMA Pinning)</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── 8. PRODUCT PREVIEW ── */}
      <section id="preview" className="py-20 border-b border-[#1F293D]/60 bg-[#0E1422]/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center space-y-3 mb-10">
            <span className="text-xs font-mono uppercase tracking-wider text-orange-400 font-semibold">
              Interactive Preview
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
              Experience the ArmPilot-AI Platform
            </h2>
            <p className="text-zinc-400 text-sm max-w-xl mx-auto">
              Explore the actual application dashboard interface built for developers and ML infrastructure engineers.
            </p>

            {/* Preview Interactive Tabs */}
            <div className="inline-flex p-1 rounded-lg bg-[#111827] border border-[#1F293D] mt-4">
              {[
                { id: "overview", label: "Dashboard" },
                { id: "benchmark", label: "Benchmark Runner" },
                { id: "recommendations", label: "AI Recommendations" },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActivePreviewTab(tab.id as any)}
                  className={`px-4 py-1.5 rounded-md text-xs font-mono font-medium transition-all ${
                    activePreviewTab === tab.id
                      ? "bg-[#EA580C] text-white shadow font-bold"
                      : "text-zinc-400 hover:text-white"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          {/* Miniature App Frame Preview */}
          <div className="rounded-2xl bg-[#0E1422] border border-[#1F293D] shadow-2xl overflow-hidden">
            {/* Top Mock Window Bar */}
            <div className="px-4 py-3 bg-[#111827] border-b border-[#1F293D] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-rose-500/70 inline-block" />
                <span className="w-3 h-3 rounded-full bg-amber-500/70 inline-block" />
                <span className="w-3 h-3 rounded-full bg-emerald-500/70 inline-block" />
                <span className="text-xs font-mono text-zinc-400 ml-3">
                  https://armpilot.dev/{activePreviewTab === "overview" ? "dashboard" : activePreviewTab === "benchmark" ? "benchmarks" : "recommendations"}
                </span>
              </div>
              <Link
                href={`/${activePreviewTab === "overview" ? "dashboard" : activePreviewTab === "benchmark" ? "benchmarks" : "recommendations"}`}
                className="text-xs font-mono text-orange-400 hover:text-orange-300 flex items-center gap-1 font-bold"
              >
                Open Full Screen →
              </Link>
            </div>

            {/* Mock Content Body */}
            <div className="p-6 bg-[#0B0F19]">
              {activePreviewTab === "overview" && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="p-3 rounded-lg bg-[#111827] border border-cyan-500/20">
                      <span className="text-[10px] font-mono text-zinc-400 block">TTFT</span>
                      <span className="text-xl font-bold font-mono text-cyan-400">48 ms</span>
                    </div>
                    <div className="p-3 rounded-lg bg-[#111827] border border-emerald-500/20">
                      <span className="text-[10px] font-mono text-zinc-400 block">TOKENS / SEC</span>
                      <span className="text-xl font-bold font-mono text-emerald-400">34.7</span>
                    </div>
                    <div className="p-3 rounded-lg bg-[#111827] border border-orange-500/20">
                      <span className="text-[10px] font-mono text-zinc-400 block">P95 LATENCY</span>
                      <span className="text-xl font-bold font-mono text-orange-400">104 ms</span>
                    </div>
                    <div className="p-3 rounded-lg bg-[#111827] border border-purple-500/20">
                      <span className="text-[10px] font-mono text-zinc-400 block">THROUGHPUT</span>
                      <span className="text-xl font-bold font-mono text-purple-400">2,840</span>
                    </div>
                  </div>

                  <div className="p-4 rounded-xl bg-[#111827] border border-[#1F293D] flex items-center justify-between text-xs font-mono">
                    <div>
                      <span className="font-bold text-white block">RUN-0042 · Llama-3.2-3B INT4</span>
                      <span className="text-zinc-400">SVE2 Vector Accelerated · 32 Threads Pinned · PASS</span>
                    </div>
                    <Link
                      href="/dashboard"
                      className="px-3 py-1.5 rounded bg-[#EA580C] text-white font-bold"
                    >
                      View Live Dashboard
                    </Link>
                  </div>
                </div>
              )}

              {activePreviewTab === "benchmark" && (
                <div className="p-4 rounded-xl bg-[#111827] border border-[#1F293D] space-y-4">
                  <div className="flex justify-between items-center text-xs font-mono">
                    <span className="text-white font-bold">Benchmark Execution: Llama-3.2-3B</span>
                    <span className="text-emerald-400 font-bold">100% COMPLETE</span>
                  </div>
                  <div className="w-full bg-[#0B0F19] rounded-full h-2.5 border border-[#1F293D]">
                    <div className="bg-gradient-to-r from-orange-600 to-amber-400 h-full rounded-full w-full" />
                  </div>
                  <div className="flex justify-end">
                    <Link href="/benchmarks" className="text-xs font-mono text-orange-400 underline">
                      Launch Benchmark Runner →
                    </Link>
                  </div>
                </div>
              )}

              {activePreviewTab === "recommendations" && (
                <div className="p-4 rounded-xl bg-[#111827] border border-orange-500/40 space-y-3">
                  <div className="flex items-center gap-2 text-xs font-mono text-orange-400 font-bold">
                    <span className="w-2 h-2 rounded-full bg-orange-500" />
                    DETECTED BOTTLENECK: Memory bandwidth saturation at 92.4%
                  </div>
                  <p className="text-xs text-zinc-300 font-sans">
                    Recommended: Switch FP16 → INT4 (GGUF Q4_K_M) + 32 pinned threads for +169% TPS.
                  </p>
                  <div className="flex justify-end">
                    <Link href="/recommendations" className="text-xs font-mono text-emerald-400 underline">
                      View Full AI Recommendations →
                    </Link>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* ── 9. FINAL CTA SECTION ── */}
      <section className="py-20 border-b border-[#1F293D]/60 relative overflow-hidden bg-gradient-to-b from-[#0B0F19] to-[#121A2C]">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-6 relative z-10">
          <div className="w-12 h-12 rounded-xl bg-orange-500/20 text-orange-400 border border-orange-500/40 flex items-center justify-center mx-auto">
            <CpuChipIcon className="w-6 h-6" />
          </div>

          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-white tracking-tight">
            Start optimizing your ARM64 AI workloads.
          </h2>

          <p className="text-zinc-300 text-sm sm:text-base max-w-xl mx-auto font-sans leading-relaxed">
            Deploy models, measure latency down to the microsecond, and unlock the full potential of your ARM64 silicon today.
          </p>

          <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/dashboard"
              className="w-full sm:w-auto px-8 py-3.5 rounded-lg bg-[#EA580C] hover:bg-[#FF7315] text-white text-sm font-bold shadow-xl shadow-orange-600/30 flex items-center justify-center gap-2 transition-all hover:scale-[1.02] cursor-pointer"
            >
              <span>Launch Dashboard</span>
              <ArrowRightIcon className="w-4 h-4" />
            </Link>

            <a
              href="#features"
              className="w-full sm:w-auto px-6 py-3.5 rounded-lg bg-[#111827] hover:bg-[#162032] text-zinc-200 hover:text-white text-sm font-medium border border-[#1F293D] flex items-center justify-center gap-2 transition-colors"
            >
              <span>View Features & Specs</span>
            </a>
          </div>
        </div>
      </section>

      {/* ── 10. FOOTER ── */}
      <footer className="py-12 bg-[#080C14] text-zinc-400 text-xs font-mono">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 border-b border-[#1F293D]/60 pb-8">
            <div className="space-y-2">
              <div className="flex items-center gap-2.5">
                <LogoIcon className="w-6 h-6 rounded-md" />
                <span className="font-bold text-sm text-white font-sans">ArmPilot-AI</span>
              </div>
              <p className="text-zinc-400 text-xs max-w-md font-sans">
                ARM64-first LLM inference optimization and benchmarking platform. Built for hackathon demo & production developer workloads.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-6 text-xs font-mono">
              <Link href="/dashboard" className="text-zinc-300 hover:text-orange-400 transition-colors">
                Product Dashboard
              </Link>
              <Link href="/inference" className="text-zinc-300 hover:text-orange-400 transition-colors">
                Model Inference
              </Link>
              <Link href="/benchmarks" className="text-zinc-300 hover:text-orange-400 transition-colors">
                Benchmark Runner
              </Link>
              <Link href="/optimization" className="text-zinc-300 hover:text-orange-400 transition-colors">
                Optimization Engine
              </Link>
              <Link href="/recommendations" className="text-zinc-300 hover:text-orange-400 transition-colors">
                AI Recommend
              </Link>
            </div>
          </div>

          <div className="pt-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-[11px] text-zinc-400">
            <div>
              © 2026 ArmPilot-AI. ARM64-First LLM Optimization Platform.
            </div>
            <div className="flex items-center gap-4">
              <span>Neoverse N1 · aarch64</span>
              <span>FastAPI + Next.js</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
