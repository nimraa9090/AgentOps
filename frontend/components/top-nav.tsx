"use client";

import React, { useState } from "react";
import {
  Search,
  Bell,
  Menu,
  Clock,
  ChevronDown,
  Layers,
  Filter,
  CheckCircle2,
  AlertTriangle,
  RotateCw,
} from "lucide-react";
import { DemoBadge } from "@/components/demo-badge";

interface TopNavProps {
  onOpenMobile: () => void;
  selectedTimeRange: string;
  onSelectTimeRange: (range: string) => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  onRefresh: () => void;
  isRefreshing: boolean;
}

const TIME_RANGES = [
  { id: "1h", label: "1h" },
  { id: "6h", label: "6h" },
  { id: "24h", label: "24h (Live)" },
  { id: "7d", label: "7d" },
];

export function TopNav({
  onOpenMobile,
  selectedTimeRange,
  onSelectTimeRange,
  searchQuery,
  onSearchChange,
  onRefresh,
  isRefreshing,
}: TopNavProps) {
  const [showNotifications, setShowNotifications] = useState(false);
  const [depthDropdownOpen, setDepthDropdownOpen] = useState(false);
  const [selectedDepth, setSelectedDepth] = useState("Hadopelagic Prod");

  const depthOptions = [
    { name: "Hadopelagic Prod", depth: "10,920m", color: "text-cyan-400" },
    { name: "Abyssopelagic Staging", depth: "6,000m", color: "text-teal-400" },
    { name: "Bathypelagic Dev", depth: "3,000m", color: "text-blue-400" },
  ];

  return (
    <header className="sticky top-0 z-30 h-16 w-full bg-[#030712]/85 backdrop-blur-md border-b border-cyan-950/70 px-4 lg:px-8 flex items-center justify-between">
      {/* Left: Mobile trigger & Breadcrumbs */}
      <div className="flex items-center gap-3">
        <button
          onClick={onOpenMobile}
          className="p-2 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800/60 lg:hidden"
          aria-label="Open sidebar"
        >
          <Menu className="w-5 h-5 text-cyan-400" />
        </button>

        <div className="hidden sm:flex items-center gap-2 text-xs font-mono">
          <span className="text-slate-400">AgentOps</span>
          <span className="text-cyan-600">/</span>
          <span className="text-slate-300">Command Center</span>
          <span className="text-cyan-600">/</span>
          <span className="text-cyan-400 font-semibold flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping"></span>
            Abyssal Telemetry
          </span>
        </div>
      </div>

      {/* Middle: Global Search Input */}
      <div className="flex-1 max-w-md mx-4 hidden md:block">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search active agents, trace IDs (e.g. trc-89410), models..."
            className="w-full pl-9 pr-4 py-1.5 bg-[#071126]/80 text-xs font-sans text-slate-200 placeholder-slate-400 rounded-lg border border-cyan-500/20 focus:outline-none focus:border-cyan-400/60 focus:ring-1 focus:ring-cyan-400/30 transition-all"
          />
          {searchQuery && (
            <button
              onClick={() => onSearchChange("")}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[10px] text-slate-400 hover:text-white px-1 py-0.5 rounded bg-slate-800"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Demo Telemetry Badge */}
        <div className="hidden xl:block">
          <DemoBadge />
        </div>

        {/* Depth Selector Dropdown */}
        <div className="relative">
          <button
            onClick={() => setDepthDropdownOpen(!depthDropdownOpen)}
            className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-[#071126] border border-cyan-500/20 text-xs font-mono text-cyan-300 hover:border-cyan-400/40 transition-colors"
          >
            <Layers className="w-3.5 h-3.5 text-cyan-400" />
            <span className="hidden sm:inline">{selectedDepth}</span>
            <ChevronDown className="w-3 h-3 text-slate-400" />
          </button>

          {depthDropdownOpen && (
            <div className="absolute right-0 mt-2 w-56 rounded-xl bg-[#060e22] border border-cyan-500/25 shadow-2xl p-1.5 z-50">
              <div className="px-2 py-1 text-[10px] font-mono uppercase text-slate-400 border-b border-slate-800">
                Depth Cluster Environment
              </div>
              {depthOptions.map((opt) => (
                <button
                  key={opt.name}
                  onClick={() => {
                    setSelectedDepth(opt.name);
                    setDepthDropdownOpen(false);
                  }}
                  className="w-full text-left px-2.5 py-2 rounded-lg text-xs hover:bg-cyan-950/40 flex items-center justify-between transition-colors"
                >
                  <span className={opt.color}>{opt.name}</span>
                  <span className="text-[10px] font-mono text-slate-400">
                    {opt.depth}
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Time Range Filters */}
        <div className="hidden lg:flex items-center bg-[#071126] border border-cyan-500/20 rounded-lg p-0.5 text-xs font-mono">
          {TIME_RANGES.map((t) => (
            <button
              key={t.id}
              onClick={() => onSelectTimeRange(t.id)}
              className={`px-2.5 py-1 rounded-md transition-all ${
                selectedTimeRange === t.id
                  ? "bg-cyan-500/20 text-cyan-300 font-semibold border border-cyan-500/30"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Refresh Button */}
        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          className="p-2 rounded-lg bg-[#071126] border border-cyan-500/20 text-slate-300 hover:text-cyan-300 hover:border-cyan-400/40 transition-colors"
          title="Refresh telemetry stream"
        >
          <RotateCw
            className={`w-4 h-4 text-cyan-400 ${
              isRefreshing ? "animate-spin" : ""
            }`}
          />
        </button>

        {/* Notifications */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="relative p-2 rounded-lg bg-[#071126] border border-cyan-500/20 text-slate-300 hover:text-cyan-300 hover:border-cyan-400/40 transition-colors"
            title="Telemetry notifications"
          >
            <Bell className="w-4 h-4 text-cyan-400" />
            <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
          </button>

          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 rounded-xl bg-[#060e22] border border-cyan-500/25 shadow-2xl p-3 z-50 text-xs">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                <span className="font-semibold text-white">Abyssal Alerts</span>
                <span className="text-[10px] font-mono text-cyan-400">
                  2 unread
                </span>
              </div>
              <div className="mt-2 space-y-2">
                <div className="p-2 rounded-lg bg-cyan-950/30 border border-cyan-500/20 flex gap-2">
                  <CheckCircle2 className="w-4 h-4 text-teal-400 shrink-0 mt-0.5" />
                  <div>
                    <p className="text-slate-200 font-medium">
                      Swarm Kraken-Router re-calibrated
                    </p>
                    <p className="text-[10px] text-slate-400 mt-0.5">
                      Subsea latency reduced by 18ms. 4m ago.
                    </p>
                  </div>
                </div>
                <div className="p-2 rounded-lg bg-amber-950/20 border border-amber-500/20 flex gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                  <div>
                    <p className="text-slate-200 font-medium">
                      DeepSeek-R1 CoT tokens spike
                    </p>
                    <p className="text-[10px] text-slate-400 mt-0.5">
                      Bathys-Researcher depth trace: 18.4k tokens. 11m ago.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* User Profile Avatar */}
        <div className="flex items-center gap-2 pl-2 border-l border-slate-800">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-600 to-teal-400 p-0.5 shadow-[0_0_10px_rgba(6,182,212,0.3)]">
            <div className="w-full h-full bg-[#040816] rounded-[7px] flex items-center justify-center font-mono text-xs font-bold text-cyan-300">
              AO
            </div>
          </div>
          <div className="hidden xl:block text-left">
            <div className="text-xs font-semibold text-slate-200">
              Cmdr. Vance
            </div>
            <div className="text-[10px] font-mono text-cyan-400/80">
              Chief Architect
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
