"use client";

import React from "react";
import {
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Info,
  Server,
  Database,
  Radio,
  Zap,
  Lock,
} from "lucide-react";
import { SystemHealthItem } from "@/types/dashboard";

interface SystemHealthProps {
  items: SystemHealthItem[];
}

const CATEGORY_ICONS = {
  Gateway: Radio,
  "Vector Lake": Database,
  "Swarm Bus": Zap,
  "LLM Circuit": Server,
  "Telemetry Stream": Lock,
};

export function SystemHealth({ items }: SystemHealthProps) {
  const getStatusIcon = (status: SystemHealthItem["status"]) => {
    switch (status) {
      case "optimal":
        return <CheckCircle2 className="w-4 h-4 text-teal-400" />;
      case "nominal":
        return <Info className="w-4 h-4 text-cyan-400" />;
      case "warning":
        return <AlertTriangle className="w-4 h-4 text-amber-400" />;
      default:
        return null;
    }
  };

  const getStatusBadge = (status: SystemHealthItem["status"]) => {
    switch (status) {
      case "optimal":
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-medium bg-teal-950/70 text-teal-300 border border-teal-500/30">
            Optimal
          </span>
        );
      case "nominal":
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-medium bg-cyan-950/70 text-cyan-300 border border-cyan-500/30">
            Nominal
          </span>
        );
      case "warning":
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-medium bg-amber-950/70 text-amber-300 border border-amber-500/30">
            Warning
          </span>
        );
      default:
        return null;
    }
  };

  return (
    <div className="ocean-card rounded-xl p-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-teal-950/60 border border-teal-500/20 text-teal-400">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <h3 className="text-base font-bold text-white tracking-tight">
              Abyssal Infrastructure & Circuit Breakers
            </h3>
            <span className="text-xs font-mono text-teal-300 bg-teal-950/70 border border-teal-800/40 px-2 py-0.5 rounded-full">
              All Systems Operational
            </span>
          </div>
          <p className="text-xs text-slate-400 font-mono mt-1">
            Subsea gateway latency, vector storage health, and provider failover circuits
          </p>
        </div>

        <div className="text-xs font-mono text-slate-400 flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-teal-400 animate-pulse" />
          <span>Gateway Pulse: 99.99%</span>
        </div>
      </div>

      {/* Health Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-3.5">
        {items.map((item) => {
          const Icon = CATEGORY_ICONS[item.category] || Server;
          return (
            <div
              key={item.id}
              className="p-3.5 rounded-xl bg-[#04091c]/80 border border-cyan-950/80 hover:border-cyan-500/30 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="p-1.5 rounded-lg bg-cyan-950/50 border border-cyan-500/20 text-cyan-300">
                    <Icon className="w-3.5 h-3.5" />
                  </div>
                  {getStatusBadge(item.status)}
                </div>

                <h4 className="text-xs font-bold text-slate-200 mb-1">
                  {item.name}
                </h4>

                <div className="text-xs font-mono font-bold text-white mb-2">
                  {item.value}
                </div>

                <p className="text-[10px] text-slate-400 leading-relaxed mb-3">
                  {item.details}
                </p>
              </div>

              <div className="pt-2 border-t border-cyan-950/60 flex items-center justify-between text-[10px] font-mono text-slate-400">
                <span className="flex items-center gap-1">
                  {getStatusIcon(item.status)}
                  <span>{item.latencyMs} ms</span>
                </span>
                <span className="text-cyan-400/80">{item.depthZone}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
