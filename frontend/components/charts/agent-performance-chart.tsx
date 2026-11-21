"use client";

import React, { useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { AgentPerformanceMetric } from "@/types/dashboard";
import { Cpu, Zap, Gauge } from "lucide-react";

interface AgentPerformanceChartProps {
  data: AgentPerformanceMetric[];
}

export function AgentPerformanceChart({ data }: AgentPerformanceChartProps) {
  const [metricKey, setMetricKey] = useState<
    "avgLatencyMs" | "tokensPerSec" | "successRate"
  >("avgLatencyMs");

  const metricConfigs = {
    avgLatencyMs: {
      label: "Latency (ms)",
      unit: "ms",
      desc: "Lower is faster",
      colors: ["#06b6d4", "#0891b2", "#0284c7", "#14b8a6", "#2dd4bf", "#38bdf8"],
    },
    tokensPerSec: {
      label: "Throughput (tokens/sec)",
      unit: "t/s",
      desc: "Higher is faster",
      colors: ["#14b8a6", "#06b6d4", "#2dd4bf", "#38bdf8", "#0891b2", "#0284c7"],
    },
    successRate: {
      label: "Success Rate (%)",
      unit: "%",
      desc: "Task resolution rate",
      colors: ["#10b981", "#14b8a6", "#06b6d4", "#2dd4bf", "#34d399", "#6ee7b7"],
    },
  };

  const currentConfig = metricConfigs[metricKey];

  return (
    <div className="ocean-card rounded-xl p-5 flex flex-col h-full">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-teal-950/60 border border-teal-500/20 text-teal-400">
              <Gauge className="w-4 h-4" />
            </div>
            <h3 className="text-base font-bold text-white tracking-tight">
              Agent Benchmark & Telemetry
            </h3>
          </div>
          <p className="text-xs text-slate-400 font-mono mt-1">
            Comparative performance across subsea agent swarms
          </p>
        </div>

        {/* Metric Selector */}
        <div className="flex items-center bg-[#071126] border border-cyan-500/20 rounded-lg p-0.5 text-xs font-mono">
          <button
            onClick={() => setMetricKey("avgLatencyMs")}
            className={`px-2.5 py-1 rounded-md transition-all ${
              metricKey === "avgLatencyMs"
                ? "bg-cyan-500/20 text-cyan-300 font-semibold border border-cyan-500/30"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Latency
          </button>
          <button
            onClick={() => setMetricKey("tokensPerSec")}
            className={`px-2.5 py-1 rounded-md transition-all ${
              metricKey === "tokensPerSec"
                ? "bg-teal-500/20 text-teal-300 font-semibold border border-teal-500/30"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Throughput
          </button>
          <button
            onClick={() => setMetricKey("successRate")}
            className={`px-2.5 py-1 rounded-md transition-all ${
              metricKey === "successRate"
                ? "bg-emerald-500/20 text-emerald-300 font-semibold border border-emerald-500/30"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Success %
          </button>
        </div>
      </div>

      {/* Bar Chart Container */}
      <div className="w-full h-72 min-h-[280px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            margin={{ top: 10, right: 10, left: -15, bottom: 25 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#0e2444"
              vertical={false}
            />

            <XAxis
              dataKey="agentName"
              stroke="#64748b"
              fontSize={10}
              tickLine={false}
              axisLine={{ stroke: "#0e2444" }}
              angle={-20}
              textAnchor="end"
              height={40}
            />

            <YAxis
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: "#0e2444" }}
              tickFormatter={(v) => `${v}${metricKey === "successRate" ? "%" : ""}`}
            />

            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const item = payload[0].payload as AgentPerformanceMetric;
                  return (
                    <div className="rounded-xl bg-[#050c1f]/95 border border-cyan-500/30 p-3 shadow-2xl backdrop-blur-md text-xs font-mono">
                      <div className="text-cyan-300 font-bold mb-1">
                        {item.agentName}
                      </div>
                      <div className="text-[10px] text-slate-400 mb-2">
                        Model: {item.model}
                      </div>
                      <div className="space-y-1 border-t border-cyan-900/40 pt-1.5 text-slate-300">
                        <div className="flex justify-between gap-4">
                          <span>{currentConfig.label}:</span>
                          <span className="font-bold text-white">
                            {item[metricKey]} {currentConfig.unit}
                          </span>
                        </div>
                        <div className="flex justify-between gap-4 text-slate-400">
                          <span>Cost Efficiency:</span>
                          <span className="text-teal-400">
                            {item.costEfficiency} / 100
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />

            <Bar
              dataKey={metricKey}
              radius={[6, 6, 0, 0]}
              maxBarSize={45}
            >
              {data.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={currentConfig.colors[index % currentConfig.colors.length]}
                  fillOpacity={0.85}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Footer Benchmark Notes */}
      <div className="mt-4 pt-3 border-t border-cyan-950/70 flex items-center justify-between text-xs font-mono text-slate-400">
        <span className="flex items-center gap-1.5">
          <Zap className="w-3.5 h-3.5 text-cyan-400" />
          Optimal tier: <strong className="text-cyan-200">Trench-Crawler</strong> (380ms)
        </span>
        <span className="text-[11px] text-slate-500">
          Normalized for reasoning CoT
        </span>
      </div>
    </div>
  );
}
