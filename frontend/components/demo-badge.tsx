"use client";

import React from "react";
import { Sparkles, Info } from "lucide-react";
import { DEMO_DATA_BADGE_TEXT } from "@/lib/mock-data";

export function DemoBadge({ className = "" }: { className?: string }) {
  return (
    <div
      className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono font-medium tracking-wide bg-cyan-950/40 border border-cyan-500/20 text-cyan-300 shadow-sm ${className}`}
      title="This dashboard is currently visualizing realistic simulated telemetry. No production backend is connected."
    >
      <span className="relative flex h-2 w-2">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
        <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
      </span>
      <span>{DEMO_DATA_BADGE_TEXT}</span>
      <Info className="w-3 h-3 text-cyan-400/80 ml-0.5" />
    </div>
  );
}
