"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LogoIcon,
  DashboardIcon,
  TerminalIcon,
  GaugeIcon,
  SlidersIcon,
  SparklesIcon,
  FileTextIcon,
  HistoryIcon,
  SettingsIcon,
  CpuChipIcon,
  ArrowRightIcon,
} from "./Icons";

interface AppLayoutProps {
  children: React.ReactNode;
  pageTitle?: string;
  headerActions?: React.ReactNode;
}

export default function AppLayout({
  children,
  pageTitle,
  headerActions,
}: AppLayoutProps) {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = [
    {
      label: "Dashboard",
      href: "/dashboard",
      icon: DashboardIcon,
    },
    {
      label: "Inference",
      href: "/inference",
      icon: TerminalIcon,
    },
    {
      label: "Benchmark",
      href: "/benchmarks",
      icon: GaugeIcon,
    },
    {
      label: "Optimization",
      href: "/optimization",
      icon: SlidersIcon,
    },
    {
      label: "AI Recommend",
      href: "/recommendations",
      icon: SparklesIcon,
      badge: "Bottleneck",
      badgeColor: "bg-amber-500/20 text-amber-400 border border-amber-500/30",
    },
    {
      label: "Reports",
      href: "/reports",
      icon: FileTextIcon,
    },
    {
      label: "History",
      href: "/history",
      icon: HistoryIcon,
    },
    {
      label: "Settings",
      href: "/settings",
      icon: SettingsIcon,
    },
  ];

  // Derive breadcrumb page name if not provided
  const currentNav = navItems.find((item) => item.href === pathname);
  const displayTitle = pageTitle || currentNav?.label || "Dashboard";

  return (
    <div className="flex h-screen w-full bg-[#0B0F19] text-[#F3F4F6] overflow-hidden font-sans">
      {/* ── Left Navigation Sidebar ── */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-64 flex flex-col justify-between border-r border-[#1F293D] bg-[#0E1422] transition-transform duration-200 lg:static lg:translate-x-0 ${
          mobileMenuOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Brand Header */}
        <div className="flex flex-col border-b border-[#1F293D] p-5">
          <div className="flex items-center justify-between">
            <Link
              href="/"
              className="flex items-center gap-3 transition-opacity hover:opacity-90 group"
            >
              <LogoIcon className="w-8 h-8 rounded-lg shadow-md shadow-orange-500/20 group-hover:scale-105 transition-transform" />
              <div>
                <span className="text-lg font-bold tracking-tight text-white flex items-center gap-1.5">
                  ArmPilot
                  <span className="text-xs font-semibold px-1.5 py-0.5 rounded bg-orange-500/15 text-orange-400 border border-orange-500/30">
                    AI
                  </span>
                </span>
                <span className="text-[11px] font-mono text-zinc-400 block -mt-0.5">
                  v2.4.1 · aarch64
                </span>
              </div>
            </Link>

            <button
              onClick={() => setMobileMenuOpen(false)}
              className="lg:hidden text-zinc-400 hover:text-white p-1"
              aria-label="Close menu"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Navigation Items List */}
        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1.5">
          <div className="px-3 pb-2 text-[11px] font-mono tracking-wider uppercase text-zinc-400">
            Platform Navigation
          </div>

          {navItems.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;

            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMobileMenuOpen(false)}
                className={`group flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                  isActive
                    ? "bg-[#EA580C] text-white shadow-lg shadow-orange-600/25 font-semibold"
                    : "text-zinc-300 hover:bg-[#162032] hover:text-white"
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon
                    className={`w-4 h-4 transition-colors ${
                      isActive
                        ? "text-white"
                        : "text-zinc-400 group-hover:text-orange-400"
                    }`}
                  />
                  <span>{item.label}</span>
                </div>

                {item.badge && !isActive && (
                  <span
                    className={`text-[10px] px-1.5 py-0.5 rounded-full font-mono font-medium ${item.badgeColor}`}
                  >
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}

          <div className="pt-4 px-3">
            <Link
              href="/"
              className="flex items-center justify-between text-xs text-zinc-400 hover:text-orange-400 py-2 border-t border-[#1F293D]/60 transition-colors group"
            >
              <span>← Back to Public Website</span>
              <ArrowRightIcon className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity" />
            </Link>
          </div>
        </nav>

        {/* Sidebar Footer System Status */}
        <div className="p-4 border-t border-[#1F293D] bg-[#0A0E18]">
          <div className="rounded-lg bg-[#111827] border border-[#1F293D] p-3 text-xs">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-400 font-semibold">
                System Status
              </span>
              <span className="flex items-center gap-1.5 text-[11px] text-emerald-400 font-medium font-mono">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-status-pulse inline-block" />
                Server Online
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2 text-[11px] font-mono text-zinc-300 pt-1 border-t border-[#1F293D]/60">
              <div>
                <span className="text-zinc-400 block text-[10px]">CPU</span>
                <span className="font-semibold text-white">84%</span> (64 cores)
              </div>
              <div>
                <span className="text-zinc-400 block text-[10px]">MEM</span>
                <span className="font-semibold text-white">3.2 GB</span> / 128G
              </div>
            </div>
          </div>
        </div>
      </aside>

      {/* Backdrop for mobile */}
      {mobileMenuOpen && (
        <div
          onClick={() => setMobileMenuOpen(false)}
          className="fixed inset-0 z-30 bg-black/60 backdrop-blur-sm lg:hidden"
        />
      )}

      {/* ── Main Content Area ── */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header */}
        <header className="h-16 border-b border-[#1F293D] bg-[#0E1422]/90 backdrop-blur-md px-4 sm:px-6 flex items-center justify-between z-10 shrink-0">
          <div className="flex items-center gap-3 sm:gap-4 min-w-0">
            {/* Mobile menu trigger */}
            <button
              onClick={() => setMobileMenuOpen(true)}
              className="lg:hidden p-2 rounded-md bg-[#162032] text-zinc-300 hover:text-white"
              aria-label="Open menu"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
            </button>

            {/* Breadcrumbs */}
            <div className="flex items-center gap-2 text-xs sm:text-sm font-mono truncate">
              <span className="text-zinc-400">armpilot</span>
              <span className="text-zinc-400">/</span>
              <span className="text-white font-medium truncate font-sans">
                {displayTitle}
              </span>
            </div>
          </div>

          {/* Top Header Right Controls & Status Chips */}
          <div className="flex items-center gap-2 sm:gap-3">
            {/* Platform Chip */}
            <div className="hidden md:flex items-center gap-2 px-2.5 py-1 rounded-md bg-[#111827] border border-[#1F293D] text-xs font-mono text-zinc-300">
              <CpuChipIcon className="w-3.5 h-3.5 text-orange-400" />
              <span>Arm Neoverse N1 · 64-core</span>
            </div>

            {/* Runtime engine chip */}
            <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#111827] border border-[#1F293D] text-xs font-mono text-zinc-300">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block" />
              <span>llama.cpp v0.3.8</span>
            </div>

            {headerActions && <div>{headerActions}</div>}

            {/* User Avatar */}
            <div className="flex items-center gap-2 pl-1 sm:pl-2">
              <div
                title="ArmPilot Admin"
                className="w-8 h-8 rounded-full bg-[#E5D5C5] text-[#2C241D] flex items-center justify-center font-bold text-xs shadow-inner cursor-pointer hover:ring-2 hover:ring-orange-500 transition-all"
              >
                A
              </div>
            </div>
          </div>
        </header>

        {/* Page Body */}
        <main className="flex-1 overflow-y-auto bg-[#0B0F19] p-4 sm:p-6 lg:p-8">
          <div className="max-w-7xl mx-auto space-y-6">{children}</div>
        </main>
      </div>
    </div>
  );
}
