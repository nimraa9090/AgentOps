"use client";

import React from "react";
import {
  Activity,
  Cpu,
  Zap,
  ShieldCheck,
  Database,
  Coins,
  TrendingUp,
  TrendingDown,
} from "lucide-react";
import { MetricCardData } from "@/types/dashboard";

const ICON_MAP = {
  Activity,
  Cpu,
  Zap,
  ShieldCheck,
  Database,
  Coins,
};

interface MetricCardProps {
  metric: MetricCardData;
}

export function MetricCard({ metric }: MetricCardProps) {
  const Icon = ICON_MAP[metric.iconName] || Activity;

  return (
    <div className="ocean-card rounded-xl p-5 relative overflow-hidden group">
      {/* Background glow orb */}
      <div className="absolute -right-6 -bottom-6 w-24 h-24 rounded-full bg-cyan-500/10 blur-xl group-hover:bg-cyan-500/20 transition-all pointer-events-none" />

      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-mono font-medium tracking-wider uppercase text-cyan-300/80">
          {metric.title}
        </span>
        <div className="p-2 rounded-lg bg-cyan-950/60 border border-cyan-500/20 text-cyan-300 group-hover:border-cyan-400/50 group-hover:text-cyan-200 transition-all shadow-[0_0_10px_rgba(6,182,212,0.1)]">
          <Icon className="w-4 h-4" />
        </div>
      </div>

      {/* Value */}
      <div className="flex items-baseline gap-2 mb-2">
        <span className="text-2xl lg:text-3xl font-bold tracking-tight text-white font-sans group-hover:text-cyan-100 transition-colors">
          {metric.value}
        </span>
      </div>

      {/* Change & Context */}
      <div className="flex items-center gap-2 mb-3">
        <span
          className={`inline-flex items-center gap-1 text-[11px] font-mono font-semibold px-1.5 py-0.5 rounded ${
            metric.isPositive
              ? "bg-teal-950/70 text-teal-300 border border-teal-500/30"
              : "bg-rose-950/70 text-rose-300 border border-rose-500/30"
          }`}
        >
          {metric.isPositive ? (
            <TrendingUp className="w-3 h-3 text-teal-400" />
          ) : (
            <TrendingDown className="w-3 h-3 text-rose-400" />
          )}
          {metric.change}
        </span>
        <span className="text-[11px] text-slate-400 font-mono">
          {metric.metricLabel}
        </span>
      </div>

      {/* Footer Info & Depth Tag */}
      <div className="pt-3 border-t border-cyan-950/70 flex items-center justify-between text-[10px] font-mono text-slate-400">
        <span className="truncate max-w-[60%]">{metric.description}</span>
        <span className="text-cyan-400/80 bg-cyan-950/40 px-1.5 py-0.5 rounded border border-cyan-900/50">
          {metric.depthTag}
        </span>
      </div>
    </div>
  );
}
