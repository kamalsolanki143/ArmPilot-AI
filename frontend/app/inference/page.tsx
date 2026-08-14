"use client";

import React, { useState } from "react";
import AppLayout from "@/components/AppLayout";
import { MOCK_MODELS, ModelItem } from "@/services/mockData";
import { apiService } from "@/services/api";
import {
  PlayIcon,
  CopyIcon,
  CheckIcon,
  ZapIcon,
  SlidersIcon,
  CpuChipIcon,
  RefreshIcon,
} from "@/components/Icons";

export default function InferencePage() {
  const [models] = useState<ModelItem[]>(MOCK_MODELS);
  const [selectedModel, setSelectedModel] = useState<ModelItem>(MOCK_MODELS[0]);
  const [prompt, setPrompt] = useState(
    "Explain how Arm Neoverse N1 and SVE2 vector instructions optimize large language model matrix multiplications compared to generic x86 AVX2 implementations."
  );
  const [output, setOutput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  // Settings
  const [maxTokens, setMaxTokens] = useState(512);
  const [temperature, setTemperature] = useState(0.7);

  // Live Metrics
  const [liveMetrics, setLiveMetrics] = useState({
    ttft: 48,
    tps: 34.7,
    memory: "3.2 GB",
    generatedTokens: 0,
  });

  const promptPresets = [
    "Explain SVE2 vectorization on Arm",
    "Benchmark INT4 vs FP16 memory traffic",
    "Optimize KV cache for low-memory ARM64",
  ];

  const handleRunInference = async () => {
    if (!prompt.trim() || isLoading) return;

    setIsLoading(true);
    setOutput("");
    setLiveMetrics((prev) => ({ ...prev, generatedTokens: 0 }));

    let tokenCount = 0;
    try {
      const result = await apiService.runInference(
        selectedModel.id,
        prompt,
        maxTokens,
        temperature,
        (tokenChunk) => {
          setOutput(tokenChunk);
          tokenCount = tokenChunk.split(/\s+/).length;
          setLiveMetrics((prev) => ({
            ...prev,
            generatedTokens: tokenCount,
          }));
        }
      );

      setLiveMetrics({
        ttft: result.ttft,
        tps: result.tps,
        memory: result.memory,
        generatedTokens: result.response.split(/\s+/).length,
      });
    } catch {
      setOutput("Error executing inference on backend.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopy = () => {
    if (!output) return;
    navigator.clipboard.writeText(output);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <AppLayout pageTitle="Model Inference">
      {/* ── Header ── */}
      <div className="pb-2 border-b border-[#1F293D]/60">
        <h1 className="text-2xl font-bold tracking-tight text-white">
          Model Inference
        </h1>
        <p className="text-xs sm:text-sm text-zinc-400 font-mono mt-1">
          Interactive inference with real-time performance monitoring & Arm vector acceleration
        </p>
      </div>

      {/* ── Select Model Horizontal Card Carousel ── */}
      <div>
        <div className="text-xs font-mono uppercase tracking-wider text-zinc-400 font-semibold mb-3 flex items-center gap-2">
          <span>Select Model</span>
          <span className="text-[11px] text-orange-400">({models.length} available)</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {models.map((model) => {
            const isSelected = selectedModel.id === model.id;
            return (
              <button
                key={model.id}
                onClick={() => setSelectedModel(model)}
                className={`p-3.5 rounded-xl text-left transition-all duration-150 relative border ${
                  isSelected
                    ? "bg-[#1E293B] border-orange-500 shadow-md shadow-orange-500/10 ring-1 ring-orange-500"
                    : "bg-[#111827] border-[#1F293D] hover:border-zinc-500 hover:bg-[#162032]"
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="font-bold text-sm text-white truncate">
                    {model.name}
                  </span>
                  {isSelected && (
                    <span className="w-2 h-2 rounded-full bg-orange-500" />
                  )}
                </div>
                <div className="flex items-center gap-2 text-xs font-mono text-zinc-400">
                  <span className="px-1.5 py-0.5 rounded bg-[#0B0F19] text-zinc-300 font-semibold text-[10px]">
                    {model.quantization}
                  </span>
                  <span>{model.size}</span>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* ── Main Layout: Center Prompt/Output + Right Sidebar ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Prompt + Output */}
        <div className="lg:col-span-2 space-y-4">
          {/* Prompt Box */}
          <div className="rounded-xl bg-[#111827] border border-[#1F293D] p-4 sm:p-5">
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-mono uppercase tracking-wider text-zinc-400 font-semibold">
                Prompt
              </label>

              <div className="flex items-center gap-1.5">
                {promptPresets.map((preset, idx) => (
                  <button
                    key={idx}
                    onClick={() => setPrompt(preset)}
                    className="hidden sm:inline-block text-[11px] px-2 py-0.5 rounded bg-[#162032] hover:bg-[#1F293D] text-zinc-300 border border-[#1F293D] transition-colors"
                  >
                    {preset}
                  </button>
                ))}
              </div>
            </div>

            <textarea
              rows={4}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Enter your prompt here..."
              className="w-full rounded-lg bg-[#0B0F19] border border-[#1F293D] p-3 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500 font-sans transition-all resize-y"
            />

            <div className="mt-3 flex items-center justify-between">
              <span className="text-xs font-mono text-zinc-400">
                Active engine: <span className="text-orange-400">{selectedModel.runtime}</span> ({selectedModel.backend})
              </span>

              <button
                onClick={handleRunInference}
                disabled={isLoading || !prompt.trim()}
                className="px-5 py-2 rounded-lg bg-[#EA580C] hover:bg-[#FF7315] disabled:opacity-50 text-white text-xs sm:text-sm font-bold shadow-lg shadow-orange-600/20 flex items-center gap-2 transition-all hover:scale-[1.02] cursor-pointer"
              >
                {isLoading ? (
                  <>
                    <RefreshIcon className="w-4 h-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <PlayIcon className="w-4 h-4" />
                    Run Inference
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Output Box */}
          <div className="rounded-xl bg-[#111827] border border-[#1F293D] p-4 sm:p-5 flex flex-col min-h-[300px]">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono uppercase tracking-wider text-zinc-400 font-semibold">
                  Output Generation
                </span>
                {isLoading && (
                  <span className="flex items-center gap-1.5 text-xs text-orange-400 font-mono">
                    <span className="w-2 h-2 rounded-full bg-orange-500 animate-pulse" />
                    Streaming...
                  </span>
                )}
              </div>

              {output && (
                <button
                  onClick={handleCopy}
                  className="px-2.5 py-1 rounded bg-[#162032] hover:bg-[#1F293D] text-xs font-mono text-zinc-300 flex items-center gap-1.5 border border-[#1F293D] transition-colors"
                >
                  {copied ? (
                    <>
                      <CheckIcon className="w-3.5 h-3.5 text-emerald-400" />
                      <span>Copied!</span>
                    </>
                  ) : (
                    <>
                      <CopyIcon className="w-3.5 h-3.5" />
                      <span>Copy</span>
                    </>
                  )}
                </button>
              )}
            </div>

            <div className="flex-1 rounded-lg bg-[#0B0F19] border border-[#1F293D] p-4 font-mono text-xs sm:text-sm text-zinc-200 overflow-y-auto whitespace-pre-wrap leading-relaxed">
              {output ? (
                output
              ) : (
                <span className="text-zinc-600 font-sans italic text-sm">
                  Output will appear here once inference is initiated...
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Right 1 Col: Generation Settings + Model Info + Live Metrics */}
        <div className="space-y-4">
          {/* Generation Settings */}
          <div className="rounded-xl bg-[#111827] border border-[#1F293D] p-4">
            <h3 className="text-xs font-mono uppercase tracking-wider text-zinc-400 font-semibold mb-3 flex items-center gap-2">
              <SlidersIcon className="w-3.5 h-3.5 text-orange-400" />
              Generation Settings
            </h3>

            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-xs font-mono mb-1">
                  <span className="text-zinc-400">Max Tokens</span>
                  <span className="text-white font-bold">{maxTokens}</span>
                </div>
                <input
                  type="range"
                  min="64"
                  max="2048"
                  step="64"
                  value={maxTokens}
                  onChange={(e) => setMaxTokens(Number(e.target.value))}
                  className="w-full cursor-pointer h-1.5 bg-[#1F293D] rounded-lg appearance-none"
                />
                <div className="flex justify-between text-[10px] font-mono text-zinc-400 mt-0.5">
                  <span>64</span>
                  <span>2048</span>
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs font-mono mb-1">
                  <span className="text-zinc-400">Temperature</span>
                  <span className="text-white font-bold">{temperature}</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="2"
                  step="0.1"
                  value={temperature}
                  onChange={(e) => setTemperature(Number(e.target.value))}
                  className="w-full cursor-pointer h-1.5 bg-[#1F293D] rounded-lg appearance-none"
                />
                <div className="flex justify-between text-[10px] font-mono text-zinc-400 mt-0.5">
                  <span>0.0 (Strict)</span>
                  <span>2.0 (Creative)</span>
                </div>
              </div>
            </div>
          </div>

          {/* Model Information */}
          <div className="rounded-xl bg-[#111827] border border-[#1F293D] p-4">
            <h3 className="text-xs font-mono uppercase tracking-wider text-zinc-400 font-semibold mb-3 flex items-center gap-2">
              <CpuChipIcon className="w-3.5 h-3.5 text-orange-400" />
              Model Information
            </h3>

            <div className="divide-y divide-[#1F293D]/60 text-xs font-mono">
              <div className="py-2 flex justify-between">
                <span className="text-zinc-400">Model</span>
                <span className="text-white font-bold">{selectedModel.name}</span>
              </div>
              <div className="py-2 flex justify-between">
                <span className="text-zinc-400">Parameters</span>
                <span className="text-zinc-200">{selectedModel.parameters}</span>
              </div>
              <div className="py-2 flex justify-between">
                <span className="text-zinc-400">Quantization</span>
                <span className="text-emerald-400 font-semibold">{selectedModel.quantization} (GGUF)</span>
              </div>
              <div className="py-2 flex justify-between">
                <span className="text-zinc-400">Model Size</span>
                <span className="text-zinc-200">{selectedModel.size}</span>
              </div>
              <div className="py-2 flex justify-between">
                <span className="text-zinc-400">Provider</span>
                <span className="text-zinc-200">{selectedModel.provider}</span>
              </div>
              <div className="py-2 flex justify-between">
                <span className="text-zinc-400">Runtime</span>
                <span className="text-orange-400">{selectedModel.runtime}</span>
              </div>
              <div className="py-2 flex justify-between">
                <span className="text-zinc-400">Backend</span>
                <span className="text-cyan-400">{selectedModel.backend}</span>
              </div>
            </div>
          </div>

          {/* Live Metrics */}
          <div className="rounded-xl bg-[#111827] border border-[#1F293D] p-4">
            <h3 className="text-xs font-mono uppercase tracking-wider text-zinc-400 font-semibold mb-3">
              Live Inference Metrics
            </h3>

            <div className="grid grid-cols-3 gap-2 text-center">
              <div className="p-2.5 rounded-lg bg-[#0B0F19] border border-cyan-500/20">
                <span className="text-[10px] font-mono text-zinc-400 block uppercase">TTFT</span>
                <span className="text-base font-bold font-mono text-cyan-400">
                  {liveMetrics.ttft}
                  <span className="text-[10px] font-normal text-zinc-400 ml-0.5">ms</span>
                </span>
              </div>

              <div className="p-2.5 rounded-lg bg-[#0B0F19] border border-emerald-500/20">
                <span className="text-[10px] font-mono text-zinc-400 block uppercase">Tokens / Sec</span>
                <span className="text-base font-bold font-mono text-emerald-400">
                  {liveMetrics.tps}
                </span>
              </div>

              <div className="p-2.5 rounded-lg bg-[#0B0F19] border border-orange-500/20">
                <span className="text-[10px] font-mono text-zinc-400 block uppercase">Memory</span>
                <span className="text-base font-bold font-mono text-orange-400">
                  {liveMetrics.memory}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
