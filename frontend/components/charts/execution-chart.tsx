"use client";

import React, { useState } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { ExecutionActivityPoint } from "@/types/dashboard";
import { Activity, ShieldCheck, AlertCircle } from "lucide-react";

interface ExecutionChartProps {
  data: ExecutionActivityPoint[];
}

export function ExecutionChart({ data }: ExecutionChartProps) {
  const [filter, setFilter] = useState<"all" | "success" | "retries">("all");

  return (
    <div className="ocean-card rounded-xl p-5 flex flex-col h-full">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-cyan-950/60 border border-cyan-500/20 text-cyan-400">
              <Activity className="w-4 h-4" />
            </div>
            <h3 className="text-base font-bold text-white tracking-tight">
              Execution Activity Stream
            </h3>
          </div>
          <p className="text-xs text-slate-400 font-mono mt-1">
            24-hour subsea trace volume & success convergence
          </p>
        </div>

        {/* Chart View Filters */}
        <div className="flex items-center bg-[#071126] border border-cyan-500/20 rounded-lg p-0.5 text-xs font-mono">
          <button
            onClick={() => setFilter("all")}
            className={`px-3 py-1 rounded-md transition-all ${
              filter === "all"
                ? "bg-cyan-500/20 text-cyan-300 font-semibold border border-cyan-500/30"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            All Activity
          </button>
          <button
            onClick={() => setFilter("success")}
            className={`px-3 py-1 rounded-md transition-all ${
              filter === "success"
                ? "bg-teal-500/20 text-teal-300 font-semibold border border-teal-500/30"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Success Only
          </button>
          <button
            onClick={() => setFilter("retries")}
            className={`px-3 py-1 rounded-md transition-all ${
              filter === "retries"
                ? "bg-amber-500/20 text-amber-300 font-semibold border border-amber-500/30"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Retries / Fails
          </button>
        </div>
      </div>

      {/* Recharts Area Container */}
      <div className="w-full h-72 min-h-[280px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={data}
            margin={{ top: 10, right: 10, left: -15, bottom: 0 }}
          >
            <defs>
              {/* Cyan gradient for Total */}
              <linearGradient id="cyanGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.0} />
              </linearGradient>
              {/* Teal gradient for Successful */}
              <linearGradient id="tealGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#14b8a6" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#14b8a6" stopOpacity={0.0} />
              </linearGradient>
              {/* Amber gradient for Retried */}
              <linearGradient id="amberGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.5} />
                <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.0} />
              </linearGradient>
            </defs>

            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#0e2444"
              vertical={false}
            />

            <XAxis
              dataKey="time"
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: "#0e2444" }}
            />

            <YAxis
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: "#0e2444" }}
              tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
            />

            <Tooltip
              content={({ active, payload, label }) => {
                if (active && payload && payload.length) {
                  return (
                    <div className="rounded-xl bg-[#050c1f]/95 border border-cyan-500/30 p-3 shadow-2xl backdrop-blur-md text-xs font-mono">
                      <div className="text-cyan-300 font-bold mb-2 pb-1 border-b border-cyan-900/50">
                        Timestamp: {label}
                      </div>
                      <div className="space-y-1">
                        {payload.map((entry, index) => (
                          <div
                            key={`item-${index}`}
                            className="flex items-center justify-between gap-4"
                          >
                            <span
                              className="capitalize flex items-center gap-1.5"
                              style={{ color: entry.color }}
                            >
                              <span
                                className="w-2 h-2 rounded-full inline-block"
                                style={{ backgroundColor: entry.color }}
                              />
                              {entry.name}:
                            </span>
                            <span className="font-bold text-white">
                              {Number(entry.value).toLocaleString()}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />

            {(filter === "all" || filter === "success") && (
              <Area
                type="monotone"
                dataKey="successful"
                name="Successful"
                stroke="#14b8a6"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#tealGradient)"
              />
            )}

            {filter === "all" && (
              <Area
                type="monotone"
                dataKey="totalExecutions"
                name="Total Volume"
                stroke="#06b6d4"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#cyanGradient)"
              />
            )}

            {(filter === "all" || filter === "retries") && (
              <Area
                type="monotone"
                dataKey="retried"
                name="Retries / Fails"
                stroke="#f59e0b"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#amberGradient)"
              />
            )}
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Footer Metrics */}
      <div className="mt-4 pt-3 border-t border-cyan-950/70 grid grid-cols-3 gap-2 text-center text-xs font-mono">
        <div className="p-2 rounded-lg bg-cyan-950/20 border border-cyan-900/30">
          <div className="text-[10px] text-slate-400">Peak Velocity</div>
          <div className="font-bold text-cyan-300 mt-0.5">15,240 / hr</div>
        </div>
        <div className="p-2 rounded-lg bg-teal-950/20 border border-teal-900/30">
          <div className="text-[10px] text-slate-400">Avg Success</div>
          <div className="font-bold text-teal-300 mt-0.5">99.41%</div>
        </div>
        <div className="p-2 rounded-lg bg-blue-950/20 border border-blue-900/30">
          <div className="text-[10px] text-slate-400">Avg Latency</div>
          <div className="font-bold text-blue-300 mt-0.5">842 ms</div>
        </div>
      </div>
    </div>
  );
}
