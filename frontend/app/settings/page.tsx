"use client";

import React, { useState } from "react";
import AppLayout from "@/components/AppLayout";
import { MOCK_HARDWARE_SPECS } from "@/services/mockData";
import { apiService } from "@/services/api";
import {
  SettingsIcon,
  CheckIcon,
  RefreshIcon,
  CpuChipIcon,
  ShieldCheckIcon,
  AlertTriangleIcon,
} from "@/components/Icons";

export default function SettingsPage() {
  const [apiUrl, setApiUrl] = useState(
    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080"
  );
  const [apiKey, setApiKey] = useState("arm-pilot-9f8a7b6c5d4e3f2a1b");
  const [testingConnection, setTestingConnection] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<"IDLE" | "SUCCESS" | "ERROR">("IDLE");

  // System Toggles
  const [darkMode, setDarkMode] = useState(true);
  const [autoOpt, setAutoOpt] = useState(false);
  const [telemetry, setTelemetry] = useState(true);

  const handleTestConnection = async () => {
    setTestingConnection(true);
    setConnectionStatus("IDLE");

    try {
      await apiService.checkHealth();
      setTimeout(() => {
        setTestingConnection(false);
        setConnectionStatus("SUCCESS");
        setTimeout(() => setConnectionStatus("IDLE"), 4000);
      }, 700);
    } catch {
      setTestingConnection(false);
      setConnectionStatus("ERROR");
    }
  };

  return (
    <AppLayout pageTitle="Settings">
      {/* ── Header ── */}
      <div className="pb-2 border-b border-[#1F293D]/60">
        <h1 className="text-2xl font-bold tracking-tight text-white">
          Settings
        </h1>
        <p className="text-xs sm:text-sm text-zinc-400 font-mono mt-1">
          API, system, hardware environment, and account configuration
        </p>
      </div>

      {/* ── 2 Column Grid ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: API Settings & System Config */}
        <div className="space-y-6">
          {/* API Settings */}
          <div className="rounded-xl bg-[#111827] border border-[#1F293D] p-5 space-y-4">
            <h2 className="text-sm font-bold text-white tracking-wide flex items-center gap-2">
              <ShieldCheckIcon className="w-4 h-4 text-orange-400" />
              API Settings
            </h2>

            <div>
              <label className="block text-xs font-mono text-zinc-400 uppercase tracking-wider mb-1.5 font-semibold">
                Inference Server URL (FastAPI Backend)
              </label>
              <input
                type="text"
                value={apiUrl}
                onChange={(e) => setApiUrl(e.target.value)}
                placeholder="http://localhost:8080"
                className="w-full rounded-lg bg-[#0B0F19] border border-[#1F293D] px-3 py-2 text-xs font-mono text-zinc-200 focus:outline-none focus:border-orange-500 transition-colors"
              />
              <span className="text-[11px] font-mono text-zinc-400 mt-1 block">
                Target endpoint set via <code className="text-orange-400">NEXT_PUBLIC_API_URL</code>
              </span>
            </div>

            <div>
              <label className="block text-xs font-mono text-zinc-400 uppercase tracking-wider mb-1.5 font-semibold">
                API Key
              </label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                className="w-full rounded-lg bg-[#0B0F19] border border-[#1F293D] px-3 py-2 text-xs font-mono text-zinc-200 focus:outline-none focus:border-orange-500 transition-colors"
              />
            </div>

            <div className="pt-1 flex items-center justify-between">
              <button
                onClick={handleTestConnection}
                disabled={testingConnection}
                className="px-4 py-2 rounded-lg bg-[#162032] hover:bg-[#1E293D] text-zinc-200 text-xs font-mono font-medium border border-[#1F293D] flex items-center gap-2 transition-colors cursor-pointer"
              >
                {testingConnection ? (
                  <>
                    <RefreshIcon className="w-3.5 h-3.5 animate-spin" />
                    Testing Ping...
                  </>
                ) : (
                  <>
                    <CheckIcon className="w-3.5 h-3.5 text-emerald-400" />
                    Test Connection
                  </>
                )}
              </button>

              {connectionStatus === "SUCCESS" && (
                <span className="text-xs font-mono text-emerald-400 flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-emerald-400" />
                  Connection verified (200 OK)
                </span>
              )}
              {connectionStatus === "ERROR" && (
                <span className="text-xs font-mono text-rose-400 flex items-center gap-1">
                  <AlertTriangleIcon className="w-3.5 h-3.5" />
                  Offline (Mock fallback active)
                </span>
              )}
            </div>
          </div>

          {/* System Configuration */}
          <div className="rounded-xl bg-[#111827] border border-[#1F293D] p-5 space-y-4">
            <h2 className="text-sm font-bold text-white tracking-wide">
              System Configuration
            </h2>

            <div className="space-y-3">
              {[
                {
                  id: "dark",
                  title: "Dark Mode",
                  desc: "High-contrast dark engineering theme",
                  checked: darkMode,
                  setter: setDarkMode,
                },
                {
                  id: "auto",
                  title: "Auto-Optimization",
                  desc: "Automatically apply recommended quantization on bottleneck detection",
                  checked: autoOpt,
                  setter: setAutoOpt,
                },
                {
                  id: "telemetry",
                  title: "Telemetry & Profiling",
                  desc: "Collect real-time CPU and memory metrics during inference",
                  checked: telemetry,
                  setter: setTelemetry,
                },
              ].map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between p-3 rounded-lg bg-[#0B0F19] border border-[#1F293D]"
                >
                  <div>
                    <div className="text-xs font-bold text-white font-mono">{item.title}</div>
                    <div className="text-[11px] text-zinc-400 font-sans">{item.desc}</div>
                  </div>

                  <button
                    type="button"
                    onClick={() => item.setter(!item.checked)}
                    className={`w-10 h-5 flex items-center rounded-full p-0.5 transition-colors cursor-pointer ${
                      item.checked ? "bg-[#EA580C]" : "bg-zinc-700"
                    }`}
                  >
                    <div
                      className={`bg-white w-4 h-4 rounded-full shadow-md transform transition-transform ${
                        item.checked ? "translate-x-5" : "translate-x-0"
                      }`}
                    />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Platform Hardware Info & Account */}
        <div className="space-y-6">
          {/* Platform Information */}
          <div className="rounded-xl bg-[#111827] border border-[#1F293D] p-5">
            <h2 className="text-sm font-bold text-white tracking-wide flex items-center gap-2 mb-4">
              <CpuChipIcon className="w-4 h-4 text-orange-400" />
              Platform Hardware Information
            </h2>

            <div className="divide-y divide-[#1F293D]/60 text-xs font-mono space-y-2">
              <div className="pt-2 flex justify-between">
                <span className="text-zinc-400">CPU</span>
                <span className="text-white font-bold">{MOCK_HARDWARE_SPECS.cpu}</span>
              </div>
              <div className="pt-2 flex justify-between">
                <span className="text-zinc-400">Memory</span>
                <span className="text-zinc-200">{MOCK_HARDWARE_SPECS.memory}</span>
              </div>
              <div className="pt-2 flex justify-between">
                <span className="text-zinc-400">OS</span>
                <span className="text-zinc-200">{MOCK_HARDWARE_SPECS.os}</span>
              </div>
              <div className="pt-2 flex justify-between">
                <span className="text-zinc-400">Kernel</span>
                <span className="text-zinc-200">{MOCK_HARDWARE_SPECS.kernel}</span>
              </div>
              <div className="pt-2 flex justify-between">
                <span className="text-zinc-400">ArmPilot Version</span>
                <span className="text-orange-400 font-bold">{MOCK_HARDWARE_SPECS.armPilotVersion}</span>
              </div>
              <div className="pt-2 flex justify-between">
                <span className="text-zinc-400">llama.cpp Engine</span>
                <span className="text-emerald-400">{MOCK_HARDWARE_SPECS.llamaCppVersion}</span>
              </div>
              <div className="pt-2 flex justify-between">
                <span className="text-zinc-400">GGUF Format</span>
                <span className="text-zinc-200">{MOCK_HARDWARE_SPECS.ggufVersion}</span>
              </div>
              <div className="pt-2 flex justify-between">
                <span className="text-zinc-400">Vector Extensions</span>
                <span className="text-cyan-400">{MOCK_HARDWARE_SPECS.instructionSets.join(", ")}</span>
              </div>
            </div>
          </div>

          {/* Account */}
          <div className="rounded-xl bg-[#111827] border border-[#1F293D] p-5">
            <h2 className="text-sm font-bold text-white tracking-wide mb-4">
              Account
            </h2>

            <div className="flex items-center gap-3.5 mb-4 p-3 rounded-lg bg-[#0B0F19] border border-[#1F293D]">
              <div className="w-10 h-10 rounded-full bg-[#E5D5C5] text-[#2C241D] flex items-center justify-center font-bold text-sm">
                A
              </div>
              <div>
                <span className="font-bold text-sm text-white block">ArmPilot Admin</span>
                <span className="text-xs font-mono text-zinc-400">admin@armpilot.dev</span>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                type="button"
                className="px-3.5 py-2 rounded-lg bg-[#162032] hover:bg-[#1E293D] text-xs font-mono text-zinc-300 border border-[#1F293D] transition-colors cursor-pointer"
              >
                Change Password
              </button>
              <button
                type="button"
                className="px-3.5 py-2 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-xs font-mono text-rose-400 border border-rose-500/30 transition-colors cursor-pointer"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
