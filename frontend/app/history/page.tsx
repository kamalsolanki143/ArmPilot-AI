"use client";

import React, { useState } from "react";
import AppLayout from "@/components/AppLayout";
import { MOCK_RUNS, RunRecord } from "@/services/mockData";
import {
  HistoryIcon,
  CheckIcon,
  ZapIcon,
  ArrowRightIcon,
  RefreshIcon,
} from "@/components/Icons";

export default function HistoryPage() {
  const [runs] = useState<RunRecord[]>(MOCK_RUNS);
  const [selectedRunIds, setSelectedRunIds] = useState<string[]>(["RUN-0042", "RUN-0041"]);
  const [compareModalOpen, setCompareModalOpen] = useState(false);

  const toggleSelect = (id: string) => {
    if (selectedRunIds.includes(id)) {
      setSelectedRunIds(selectedRunIds.filter((item) => item !== id));
    } else {
      if (selectedRunIds.length >= 2) {
        // Replace second selection
        setSelectedRunIds([selectedRunIds[0], id]);
      } else {
        setSelectedRunIds([...selectedRunIds, id]);
      }
    }
  };

  const run1 = runs.find((r) => r.id === selectedRunIds[0]);
  const run2 = runs.find((r) => r.id === selectedRunIds[1]);

  return (
    <AppLayout pageTitle="Run History">
      {/* ── Header ── */}
      <div className="pb-2 border-b border-[#1F293D]/60 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Run History
          </h1>
          <p className="text-xs sm:text-sm text-zinc-400 font-mono mt-1">
            Historical benchmark executions · Select up to 2 runs to compare side-by-side
          </p>
        </div>

        {/* Compare CTA */}
        {selectedRunIds.length === 2 && (
          <button
            onClick={() => setCompareModalOpen(true)}
            className="px-4 py-2 rounded-lg bg-[#EA580C] hover:bg-[#FF7315] text-white text-xs font-mono font-bold shadow-lg shadow-orange-600/25 flex items-center gap-2 transition-all hover:scale-[1.02] cursor-pointer"
          >
            <span>Compare Selected ({selectedRunIds.join(" vs ")}) →</span>
          </button>
        )}
      </div>

      {/* ── Table of Runs ── */}
      <div className="rounded-xl bg-[#111827] border border-[#1F293D] overflow-hidden">
        <div className="p-4 border-b border-[#1F293D] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-zinc-400">
              Selected: <strong className="text-white">{selectedRunIds.length}</strong> / 2 runs
            </span>
          </div>

          {selectedRunIds.length > 0 && (
            <button
              onClick={() => setSelectedRunIds([])}
              className="text-xs font-mono text-zinc-400 hover:text-white underline"
            >
              Clear selection
            </button>
          )}
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-[#0E1422] text-zinc-400 border-b border-[#1F293D] uppercase text-[11px]">
              <tr>
                <th className="py-3 px-4 w-10">Select</th>
                <th className="py-3 px-4 font-semibold">Run ID</th>
                <th className="py-3 px-4 font-semibold">Model</th>
                <th className="py-3 px-4 font-semibold">Configuration</th>
                <th className="py-3 px-4 font-semibold">TTFT</th>
                <th className="py-3 px-4 font-semibold">Tokens / Sec</th>
                <th className="py-3 px-4 font-semibold">P95 Latency</th>
                <th className="py-3 px-4 font-semibold">Status</th>
                <th className="py-3 px-4 font-semibold">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1F293D]/60 text-zinc-300">
              {runs.map((run) => {
                const isSelected = selectedRunIds.includes(run.id);

                return (
                  <tr
                    key={run.id}
                    onClick={() => toggleSelect(run.id)}
                    className={`cursor-pointer transition-colors ${
                      isSelected
                        ? "bg-[#1E293B]/70"
                        : "hover:bg-[#162032]"
                    }`}
                  >
                    <td className="py-3.5 px-4" onClick={(e) => e.stopPropagation()}>
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => toggleSelect(run.id)}
                        className="rounded bg-[#0B0F19] border-[#1F293D] text-orange-500 focus:ring-orange-500 cursor-pointer"
                      />
                    </td>
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
                    <td className="py-3.5 px-4 text-zinc-400 text-[11px]">{run.date}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Side-by-Side Compare Modal ── */}
      {compareModalOpen && run1 && run2 && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fadeIn">
          <div className="w-full max-w-3xl rounded-xl bg-[#111827] border border-[#1F293D] shadow-2xl p-6 space-y-5 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-[#1F293D] pb-3">
              <div>
                <h3 className="text-base font-bold text-white font-mono">
                  Benchmark Run Comparison
                </h3>
                <p className="text-xs text-zinc-400 font-mono">
                  {run1.id} ({run1.config}) vs {run2.id} ({run2.config})
                </p>
              </div>
              <button
                onClick={() => setCompareModalOpen(false)}
                className="text-zinc-400 hover:text-white p-1"
              >
                ✕
              </button>
            </div>

            {/* Comparison Grid */}
            <div className="grid grid-cols-2 gap-4">
              {/* Run 1 Card */}
              <div className="rounded-lg bg-[#0B0F19] border border-[#1F293D] p-4">
                <div className="flex justify-between items-center mb-3">
                  <span className="font-bold text-white font-mono text-sm">{run1.id}</span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 font-mono">
                    {run1.status}
                  </span>
                </div>
                <div className="space-y-2 text-xs font-mono">
                  <div className="flex justify-between"><span className="text-zinc-400">Model:</span> <span className="text-white">{run1.model}</span></div>
                  <div className="flex justify-between"><span className="text-zinc-400">Config:</span> <span className="text-white">{run1.config}</span></div>
                  <div className="flex justify-between"><span className="text-zinc-400">TTFT:</span> <span className="text-cyan-400 font-bold">{run1.ttft}</span></div>
                  <div className="flex justify-between"><span className="text-zinc-400">Tokens/sec:</span> <span className="text-emerald-400 font-bold">{run1.tps}</span></div>
                  <div className="flex justify-between"><span className="text-zinc-400">P95 Latency:</span> <span className="text-orange-400 font-bold">{run1.p95}</span></div>
                  <div className="flex justify-between"><span className="text-zinc-400">Memory:</span> <span className="text-zinc-300">{run1.memory}</span></div>
                  <div className="flex justify-between"><span className="text-zinc-400">CPU Util:</span> <span className="text-zinc-300">{run1.cpu}</span></div>
                </div>
              </div>

              {/* Run 2 Card */}
              <div className="rounded-lg bg-[#0B0F19] border border-emerald-500/30 p-4">
                <div className="flex justify-between items-center mb-3">
                  <span className="font-bold text-white font-mono text-sm">{run2.id}</span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 font-mono">
                    {run2.status}
                  </span>
                </div>
                <div className="space-y-2 text-xs font-mono">
                  <div className="flex justify-between"><span className="text-zinc-400">Model:</span> <span className="text-white">{run2.model}</span></div>
                  <div className="flex justify-between"><span className="text-zinc-400">Config:</span> <span className="text-white">{run2.config}</span></div>
                  <div className="flex justify-between"><span className="text-zinc-400">TTFT:</span> <span className="text-cyan-400 font-bold">{run2.ttft}</span></div>
                  <div className="flex justify-between"><span className="text-zinc-400">Tokens/sec:</span> <span className="text-emerald-400 font-bold">{run2.tps}</span></div>
                  <div className="flex justify-between"><span className="text-zinc-400">P95 Latency:</span> <span className="text-orange-400 font-bold">{run2.p95}</span></div>
                  <div className="flex justify-between"><span className="text-zinc-400">Memory:</span> <span className="text-zinc-300">{run2.memory}</span></div>
                  <div className="flex justify-between"><span className="text-zinc-400">CPU Util:</span> <span className="text-zinc-300">{run2.cpu}</span></div>
                </div>
              </div>
            </div>

            {/* Delta summary */}
            <div className="rounded-lg bg-[#0E1422] border border-[#1F293D] p-4 text-xs font-mono">
              <span className="font-bold text-white block mb-2">Performance Delta ({run1.id} → {run2.id}):</span>
              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="p-2 rounded bg-[#111827]">
                  <span className="text-[10px] text-zinc-400 block">Throughput Delta</span>
                  <span className="text-sm font-bold text-emerald-400">
                    {run2.tps > run1.tps ? `+${((run2.tps / run1.tps - 1) * 100).toFixed(0)}%` : `${((run2.tps / run1.tps - 1) * 100).toFixed(0)}%`}
                  </span>
                </div>
                <div className="p-2 rounded bg-[#111827]">
                  <span className="text-[10px] text-zinc-400 block">TTFT Delta</span>
                  <span className="text-sm font-bold text-cyan-400">
                    {parseInt(run2.ttft) < parseInt(run1.ttft) ? `-${Math.round((1 - parseInt(run2.ttft)/parseInt(run1.ttft))*100)}%` : "+15%"}
                  </span>
                </div>
                <div className="p-2 rounded bg-[#111827]">
                  <span className="text-[10px] text-zinc-400 block">P95 Delta</span>
                  <span className="text-sm font-bold text-orange-400">
                    {parseInt(run2.p95) < parseInt(run1.p95) ? `-${Math.round((1 - parseInt(run2.p95)/parseInt(run1.p95))*100)}%` : "+20%"}
                  </span>
                </div>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setCompareModalOpen(false)}
                className="px-4 py-2 rounded-lg bg-[#EA580C] hover:bg-[#FF7315] text-xs font-mono font-bold text-white cursor-pointer"
              >
                Close Comparison
              </button>
            </div>
          </div>
        </div>
      )}
    </AppLayout>
  );
}
