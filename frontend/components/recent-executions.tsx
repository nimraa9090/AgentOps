"use client";

import React, { useState } from "react";
import {
  Route,
  CheckCircle2,
  Clock,
  AlertTriangle,
  XCircle,
  ExternalLink,
  Copy,
  Check,
  Filter,
  FileCode,
  Shield,
  Layers,
} from "lucide-react";
import { ExecutionTrace } from "@/types/dashboard";

interface RecentExecutionsProps {
  traces: ExecutionTrace[];
  searchQuery: string;
}

export function RecentExecutions({ traces, searchQuery }: RecentExecutionsProps) {
  const [selectedTrace, setSelectedTrace] = useState<ExecutionTrace | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("all");

  const filteredTraces = traces.filter((trace) => {
    const q = searchQuery.toLowerCase();
    const matchesSearch =
      trace.id.toLowerCase().includes(q) ||
      trace.agentName.toLowerCase().includes(q) ||
      trace.modelUsed.toLowerCase().includes(q) ||
      trace.triggerType.toLowerCase().includes(q) ||
      trace.depthZone.toLowerCase().includes(q);

    const matchesStatus =
      statusFilter === "all" || trace.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  const handleCopy = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(id);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const getStatusBadge = (status: ExecutionTrace["status"]) => {
    switch (status) {
      case "completed":
        return (
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-mono bg-teal-950/80 text-teal-300 border border-teal-500/30">
            <CheckCircle2 className="w-3 h-3 text-teal-400" />
            Completed
          </span>
        );
      case "running":
        return (
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-mono bg-cyan-950/80 text-cyan-300 border border-cyan-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping" />
            Running
          </span>
        );
      case "degraded":
        return (
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-mono bg-amber-950/80 text-amber-300 border border-amber-500/30">
            <AlertTriangle className="w-3 h-3 text-amber-400" />
            Degraded
          </span>
        );
      case "failed":
        return (
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-mono bg-rose-950/80 text-rose-300 border border-rose-500/30">
            <XCircle className="w-3 h-3 text-rose-400" />
            Failed
          </span>
        );
      default:
        return null;
    }
  };

  return (
    <div className="ocean-card rounded-xl p-5">
      {/* Table Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-cyan-950/60 border border-cyan-500/20 text-cyan-400">
              <Route className="w-4 h-4" />
            </div>
            <h3 className="text-base font-bold text-white tracking-tight">
              Recent Execution Traces
            </h3>
            <span className="text-xs font-mono text-cyan-300 bg-cyan-950/70 border border-cyan-800/40 px-2 py-0.5 rounded-full">
              Live Stream
            </span>
          </div>
          <p className="text-xs text-slate-400 font-mono mt-1">
            End-to-end multi-agent execution spans, token usage, and cost accounting
          </p>
        </div>

        {/* Status Filters */}
        <div className="flex items-center bg-[#071126] border border-cyan-500/20 rounded-lg p-0.5 text-xs font-mono">
          {["all", "completed", "running", "degraded"].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-2.5 py-1 rounded-md capitalize transition-all ${
                statusFilter === st
                  ? "bg-cyan-500/20 text-cyan-300 font-semibold border border-cyan-500/30"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Table Container */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs font-mono border-collapse">
          <thead>
            <tr className="border-b border-cyan-950/80 text-cyan-400/70 uppercase text-[10px] tracking-wider bg-[#040919]/50">
              <th className="py-3 px-3">Trace ID</th>
              <th className="py-3 px-3">Agent</th>
              <th className="py-3 px-3">Trigger</th>
              <th className="py-3 px-3">Model</th>
              <th className="py-3 px-3 text-right">Tokens</th>
              <th className="py-3 px-3 text-right">Cost</th>
              <th className="py-3 px-3 text-right">Latency</th>
              <th className="py-3 px-3">Status</th>
              <th className="py-3 px-3">Timestamp</th>
              <th className="py-3 px-3 text-center">Inspect</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-cyan-950/40">
            {filteredTraces.length === 0 ? (
              <tr>
                <td colSpan={10} className="py-10 text-center text-slate-500">
                  No execution traces found matching current filter.
                </td>
              </tr>
            ) : (
              filteredTraces.map((trace) => (
                <tr
                  key={trace.id}
                  onClick={() => setSelectedTrace(trace)}
                  className="hover:bg-cyan-950/20 cursor-pointer transition-colors group"
                >
                  {/* Trace ID */}
                  <td className="py-3 px-3 text-cyan-300 font-medium">
                    <div className="flex items-center gap-1.5">
                      <span>{trace.id}</span>
                      <button
                        onClick={(e) => handleCopy(trace.id, e)}
                        className="text-slate-500 hover:text-cyan-400 transition-colors"
                        title="Copy Trace ID"
                      >
                        {copiedId === trace.id ? (
                          <Check className="w-3 h-3 text-teal-400" />
                        ) : (
                          <Copy className="w-3 h-3 opacity-0 group-hover:opacity-100" />
                        )}
                      </button>
                    </div>
                  </td>

                  {/* Agent */}
                  <td className="py-3 px-3 text-white font-sans font-semibold">
                    <div className="flex items-center gap-2">
                      <div className="w-5 h-5 rounded bg-cyan-950 border border-cyan-500/30 flex items-center justify-center text-[10px] text-cyan-300">
                        {trace.agentName.charAt(0)}
                      </div>
                      <span>{trace.agentName}</span>
                    </div>
                  </td>

                  {/* Trigger */}
                  <td className="py-3 px-3 text-slate-300">
                    <span className="px-2 py-0.5 rounded bg-slate-800/60 border border-slate-700/50 text-[10px]">
                      {trace.triggerType}
                    </span>
                  </td>

                  {/* Model */}
                  <td className="py-3 px-3 text-slate-400">
                    <span className="text-[11px] text-blue-300">
                      {trace.modelUsed}
                    </span>
                  </td>

                  {/* Tokens */}
                  <td className="py-3 px-3 text-right text-slate-200">
                    {trace.tokensConsumed.toLocaleString()}
                  </td>

                  {/* Cost */}
                  <td className="py-3 px-3 text-right text-teal-400">
                    ${trace.costEstimateUsd.toFixed(4)}
                  </td>

                  {/* Latency */}
                  <td className="py-3 px-3 text-right text-cyan-300">
                    {trace.latencyMs} ms
                  </td>

                  {/* Status */}
                  <td className="py-3 px-3">
                    {getStatusBadge(trace.status)}
                  </td>

                  {/* Timestamp */}
                  <td className="py-3 px-3 text-slate-400">
                    {trace.timestamp}
                  </td>

                  {/* Inspect Button */}
                  <td className="py-3 px-3 text-center">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedTrace(trace);
                      }}
                      className="p-1 rounded text-slate-400 hover:text-cyan-300 hover:bg-cyan-950/50"
                      title="Inspect Trace Breakdown"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Trace Inspection Modal / Drawer */}
      {selectedTrace && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="w-full max-w-xl ocean-card rounded-2xl p-6 border border-cyan-500/30 text-xs font-mono shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-cyan-950">
              <div className="flex items-center gap-2">
                <FileCode className="w-4 h-4 text-cyan-400" />
                <span className="font-bold text-white text-sm">
                  Trace Details: {selectedTrace.id}
                </span>
              </div>
              <button
                onClick={() => setSelectedTrace(null)}
                className="text-slate-400 hover:text-white px-2 py-1 rounded bg-slate-800"
              >
                Close
              </button>
            </div>

            <div className="my-4 space-y-3">
              <div className="grid grid-cols-2 gap-3 p-3 rounded-lg bg-[#040a1b] border border-cyan-950">
                <div>
                  <span className="text-slate-400 block text-[10px]">Agent Assigned:</span>
                  <span className="text-cyan-300 font-bold">{selectedTrace.agentName}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px]">Model Architecture:</span>
                  <span className="text-white">{selectedTrace.modelUsed}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px]">Operational Depth:</span>
                  <span className="text-teal-300">{selectedTrace.depthZone}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px]">Execution Latency:</span>
                  <span className="text-cyan-400 font-bold">{selectedTrace.latencyMs} ms</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px]">Token Consumption:</span>
                  <span className="text-white">{selectedTrace.tokensConsumed.toLocaleString()} tokens</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px]">Calculated Cost:</span>
                  <span className="text-teal-400 font-bold">${selectedTrace.costEstimateUsd.toFixed(4)}</span>
                </div>
              </div>

              <div className="p-3 rounded-lg bg-[#040a1b] border border-cyan-950 space-y-2">
                <span className="text-slate-400 font-semibold block text-[11px]">
                  Subsea Step Decomposition:
                </span>
                <div className="space-y-1.5 text-[11px] text-slate-300">
                  <div className="flex items-center justify-between p-1.5 rounded bg-cyan-950/20 border border-cyan-900/30">
                    <span>1. Ingest Prompt & Validate Circuit Breakers</span>
                    <span className="text-teal-400 font-bold">14 ms</span>
                  </div>
                  <div className="flex items-center justify-between p-1.5 rounded bg-cyan-950/20 border border-cyan-900/30">
                    <span>2. Chroma Vector Retrieval (14.8M embeddings)</span>
                    <span className="text-teal-400 font-bold">42 ms</span>
                  </div>
                  <div className="flex items-center justify-between p-1.5 rounded bg-cyan-950/20 border border-cyan-900/30">
                    <span>3. Multi-hop LLM Reasoning Execution</span>
                    <span className="text-cyan-300 font-bold">{selectedTrace.latencyMs - 74} ms</span>
                  </div>
                  <div className="flex items-center justify-between p-1.5 rounded bg-cyan-950/20 border border-cyan-900/30">
                    <span>4. Leviathan PII Sanitizer & Audit Seal</span>
                    <span className="text-teal-400 font-bold">18 ms</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="pt-3 border-t border-cyan-950 flex justify-between items-center text-[11px] text-slate-500">
              <span>Telemetry Verified • Zero-Knowledge Hash</span>
              <button
                onClick={() => setSelectedTrace(null)}
                className="px-3 py-1.5 rounded-lg bg-cyan-600 text-white font-semibold hover:bg-cyan-500"
              >
                Dismiss
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
