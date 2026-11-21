"use client";

import React, { useState } from "react";
import {
  Bot,
  Activity,
  Layers,
  Cpu,
  Clock,
  Sparkles,
  ChevronRight,
  ShieldCheck,
  CheckCircle,
  Play,
  RotateCw,
} from "lucide-react";
import { AgentInfo } from "@/types/dashboard";

interface ActiveAgentsProps {
  agents: AgentInfo[];
  searchQuery: string;
}

export function ActiveAgents({ agents, searchQuery }: ActiveAgentsProps) {
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);

  const filteredAgents = agents.filter((agent) => {
    const q = searchQuery.toLowerCase();
    return (
      agent.name.toLowerCase().includes(q) ||
      agent.role.toLowerCase().includes(q) ||
      agent.model.toLowerCase().includes(q) ||
      agent.codenamedDepth.toLowerCase().includes(q)
    );
  });

  const getStatusBadge = (status: AgentInfo["status"]) => {
    switch (status) {
      case "active":
        return (
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-mono font-medium bg-teal-950/80 text-teal-300 border border-teal-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-pulse" />
            Active
          </span>
        );
      case "computing":
        return (
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-mono font-medium bg-cyan-950/80 text-cyan-300 border border-cyan-500/30">
            <RotateCw className="w-2.5 h-2.5 text-cyan-400 animate-spin" />
            Computing
          </span>
        );
      case "idle":
        return (
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-mono font-medium bg-slate-900/80 text-slate-400 border border-slate-700/50">
            <span className="w-1.5 h-1.5 rounded-full bg-slate-500" />
            Standby
          </span>
        );
      default:
        return null;
    }
  };

  return (
    <div className="ocean-card rounded-xl p-5">
      {/* Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-cyan-950/60 border border-cyan-500/20 text-cyan-400">
              <Bot className="w-4 h-4" />
            </div>
            <h3 className="text-base font-bold text-white tracking-tight">
              Active Subsea Agent Swarm
            </h3>
            <span className="text-xs font-mono text-cyan-300 bg-cyan-950/70 border border-cyan-800/40 px-2 py-0.5 rounded-full">
              {filteredAgents.length} Online
            </span>
          </div>
          <p className="text-xs text-slate-400 font-mono mt-1">
            Real-time telemetry and task decomposition across operational depth layers
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
          <span>Depth: 150m → 10,920m</span>
        </div>
      </div>

      {/* Agents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {filteredAgents.length === 0 ? (
          <div className="col-span-full py-12 text-center text-slate-500 font-mono text-sm">
            No agents found matching &ldquo;{searchQuery}&rdquo;
          </div>
        ) : (
          filteredAgents.map((agent) => {
            const isSelected = selectedAgentId === agent.id;
            return (
              <div
                key={agent.id}
                onClick={() =>
                  setSelectedAgentId(isSelected ? null : agent.id)
                }
                className={`relative rounded-xl p-4 bg-[#050e24]/80 border transition-all cursor-pointer ${
                  isSelected
                    ? "border-cyan-400/60 bg-[#071638] shadow-[0_0_20px_rgba(6,182,212,0.2)]"
                    : "border-cyan-950 hover:border-cyan-500/30 hover:bg-[#06122d]"
                }`}
              >
                {/* Agent Header */}
                <div className="flex items-start justify-between gap-2 mb-2.5">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-950 to-blue-900 border border-cyan-500/30 flex items-center justify-center text-cyan-300">
                      <Bot className="w-4 h-4" />
                    </div>
                    <div>
                      <h4 className="text-xs font-bold text-white group-hover:text-cyan-200">
                        {agent.name}
                      </h4>
                      <p className="text-[10px] font-mono text-cyan-400/80">
                        {agent.codenamedDepth}
                      </p>
                    </div>
                  </div>
                  {getStatusBadge(agent.status)}
                </div>

                {/* Role & Model */}
                <div className="mb-3 space-y-1">
                  <div className="text-[11px] text-slate-300 font-medium">
                    {agent.role}
                  </div>
                  <div className="inline-block text-[10px] font-mono px-2 py-0.5 rounded bg-blue-950/50 text-blue-300 border border-blue-900/40">
                    {agent.model}
                  </div>
                </div>

                {/* Current Task Box */}
                <div className="p-2.5 rounded-lg bg-[#030816]/70 border border-cyan-950/80 text-[11px] text-slate-300 mb-3">
                  <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 mb-1">
                    <span>Current Subsea Task</span>
                    <span className="text-teal-400">Step In Progress</span>
                  </div>
                  <p className="line-clamp-2 italic text-slate-300">
                    &ldquo;{agent.currentTask}&rdquo;
                  </p>
                </div>

                {/* Metrics Breakdown */}
                <div className="grid grid-cols-3 gap-2 pt-2 border-t border-cyan-950/60 text-center font-mono">
                  <div className="p-1.5 rounded bg-cyan-950/20">
                    <div className="text-[9px] text-slate-400">Latency</div>
                    <div className="text-xs font-bold text-cyan-300 mt-0.5">
                      {agent.avgLatencyMs} ms
                    </div>
                  </div>
                  <div className="p-1.5 rounded bg-teal-950/20">
                    <div className="text-[9px] text-slate-400">Success</div>
                    <div className="text-xs font-bold text-teal-300 mt-0.5">
                      {agent.successRatePercent}%
                    </div>
                  </div>
                  <div className="p-1.5 rounded bg-blue-950/20">
                    <div className="text-[9px] text-slate-400">RAM</div>
                    <div className="text-xs font-bold text-blue-300 mt-0.5">
                      {agent.memoryUsageMb} MB
                    </div>
                  </div>
                </div>

                {/* Expanded Details Drawer */}
                {isSelected && (
                  <div className="mt-3 pt-3 border-t border-cyan-500/20 text-xs font-mono space-y-1.5 text-slate-300">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Tokens Processed:</span>
                      <span className="text-white font-bold">
                        {agent.tokensProcessed.toLocaleString()}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Subsea Uptime:</span>
                      <span className="text-teal-300">{agent.uptimeHours} hrs</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Execution Depth:</span>
                      <span className="text-cyan-300">
                        {agent.operationalDepthMeters.toLocaleString()} meters
                      </span>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
