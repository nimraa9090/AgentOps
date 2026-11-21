"use client";

import React, { useState } from "react";
import { Sidebar } from "@/components/sidebar";
import { TopNav } from "@/components/top-nav";
import { MetricCard } from "@/components/metric-card";
import { ExecutionChart } from "@/components/charts/execution-chart";
import { AgentPerformanceChart } from "@/components/charts/agent-performance-chart";
import { ActiveAgents } from "@/components/active-agents";
import { RecentExecutions } from "@/components/recent-executions";
import { SystemHealth } from "@/components/system-health";
import { DemoBadge } from "@/components/demo-badge";
import {
  OVERVIEW_METRICS,
  EXECUTION_ACTIVITY_DATA,
  AGENT_PERFORMANCE_DATA,
  ACTIVE_AGENTS,
  RECENT_EXECUTIONS,
  SYSTEM_HEALTH_ITEMS,
} from "@/lib/mock-data";
import {
  Compass,
  Play,
  Download,
  Terminal,
  Activity,
  Layers,
  Sparkles,
  RefreshCw,
  Waves,
} from "lucide-react";

export default function DashboardPage() {
  const [activeSection, setActiveSection] = useState<string>("overview");
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState<boolean>(false);
  const [selectedTimeRange, setSelectedTimeRange] = useState<string>("24h");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [feedbackToast, setFeedbackToast] = useState<string | null>(null);

  const showToast = (message: string) => {
    setFeedbackToast(message);
    setTimeout(() => {
      setFeedbackToast(null);
    }, 3500);
  };

  const handleRefresh = () => {
    setIsRefreshing(true);
    showToast("Telemetry stream synchronized with Subsea Cluster Alpha.");
    setTimeout(() => {
      setIsRefreshing(false);
    }, 1200);
  };

  const handleSimulateTrace = () => {
    showToast("Simulated autonomous trace dispatched to Kraken-Router swarm.");
  };

  const handleExportAudit = () => {
    showToast("Telemetry audit report generated (Simulated CSV/JSON).");
  };

  return (
    <div className="min-h-screen bg-[#030712] text-slate-100 flex flex-col">
      {/* Background Deep Ocean Ambient Glows */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
        <div className="absolute -top-40 -left-40 w-[600px] h-[600px] rounded-full bg-cyan-900/10 blur-[130px]" />
        <div className="absolute top-1/3 -right-40 w-[500px] h-[500px] rounded-full bg-teal-900/10 blur-[140px]" />
        <div className="absolute -bottom-40 left-1/3 w-[700px] h-[700px] rounded-full bg-blue-950/20 blur-[150px]" />
      </div>

      {/* Floating Notification Toast */}
      {feedbackToast && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2.5 px-4 py-3 rounded-xl bg-[#06122d]/95 border border-cyan-400/50 shadow-[0_0_20px_rgba(6,182,212,0.3)] text-xs font-mono text-cyan-200 animate-in fade-in slide-in-from-bottom-4">
          <Sparkles className="w-4 h-4 text-cyan-400" />
          <span>{feedbackToast}</span>
        </div>
      )}

      {/* Sidebar Navigation */}
      <Sidebar
        activeSection={activeSection}
        onSelectSection={(sec) => {
          setActiveSection(sec);
          if (sec !== "overview") {
            showToast(`Switched view to '${sec}' (Viewing Overview telemetric stream).`);
          }
        }}
        mobileOpen={mobileSidebarOpen}
        onCloseMobile={() => setMobileSidebarOpen(false)}
      />

      {/* Main Layout Area */}
      <div className="flex-1 lg:pl-72 flex flex-col min-w-0 relative z-10">
        {/* Top Navigation Bar */}
        <TopNav
          onOpenMobile={() => setMobileSidebarOpen(true)}
          selectedTimeRange={selectedTimeRange}
          onSelectTimeRange={(range) => {
            setSelectedTimeRange(range);
            showToast(`Time window adjusted to ${range}.`);
          }}
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          onRefresh={handleRefresh}
          isRefreshing={isRefreshing}
        />

        {/* Dashboard Content Container */}
        <main className="flex-1 p-4 lg:p-8 space-y-6 max-w-7xl w-full mx-auto">
          {/* Hero Command Banner */}
          <div className="ocean-card rounded-2xl p-6 relative overflow-hidden">
            <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="space-y-1.5">
                <div className="flex items-center gap-2.5 flex-wrap">
                  <h1 className="text-xl sm:text-2xl lg:text-3xl font-extrabold text-white tracking-tight">
                    AgentOps
                    <span className="text-cyan-400 font-light ml-2">
                      — Abyssal Intelligence
                    </span>
                  </h1>
                  <DemoBadge className="my-0.5" />
                </div>
                <p className="text-xs sm:text-sm text-slate-400 font-mono flex items-center gap-1.5">
                  <Waves className="w-4 h-4 text-cyan-400 shrink-0" />
                  <span>
                    Deep-sea autonomous swarm telemetry • Operational Depth:{" "}
                    <strong className="text-cyan-300">10,920m (Hadopelagic Zone)</strong>
                  </span>
                </p>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2.5 flex-wrap">
                <button
                  onClick={handleSimulateTrace}
                  className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-gradient-to-r from-cyan-600 to-teal-600 text-white text-xs font-mono font-semibold hover:from-cyan-500 hover:to-teal-500 transition-all shadow-[0_0_15px_rgba(6,182,212,0.3)] active:scale-95"
                >
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>Simulate Trace</span>
                </button>

                <button
                  onClick={handleExportAudit}
                  className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-[#07132c] border border-cyan-500/25 text-slate-300 text-xs font-mono font-medium hover:text-cyan-300 hover:border-cyan-400/50 transition-all active:scale-95"
                >
                  <Download className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Export Telemetry</span>
                </button>
              </div>
            </div>
          </div>

          {/* 1. Overview Analytics Cards (KPIs) */}
          <section aria-label="Key Performance Indicators">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
              {OVERVIEW_METRICS.map((metric) => (
                <MetricCard key={metric.id} metric={metric} />
              ))}
            </div>
          </section>

          {/* 2. Visual Analytics Charts Grid */}
          <section
            aria-label="Charts Section"
            className="grid grid-cols-1 lg:grid-cols-2 gap-6 min-w-0"
          >
            {/* Execution Activity Chart */}
            <div className="min-w-0">
              <ExecutionChart data={EXECUTION_ACTIVITY_DATA} />
            </div>

            {/* Agent Performance Chart */}
            <div className="min-w-0">
              <AgentPerformanceChart data={AGENT_PERFORMANCE_DATA} />
            </div>
          </section>

          {/* 3. Active Subsea Agent Swarm */}
          <section aria-label="Active Swarm">
            <ActiveAgents agents={ACTIVE_AGENTS} searchQuery={searchQuery} />
          </section>

          {/* 4. Infrastructure Health & Circuit Breakers */}
          <section aria-label="System Health">
            <SystemHealth items={SYSTEM_HEALTH_ITEMS} />
          </section>

          {/* 5. Recent Execution Traces */}
          <section aria-label="Recent Executions">
            <RecentExecutions
              traces={RECENT_EXECUTIONS}
              searchQuery={searchQuery}
            />
          </section>

          {/* Ocean Dashboard Footer */}
          <footer className="pt-8 pb-12 border-t border-cyan-950/60 text-xs font-mono text-slate-500 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <Compass className="w-4 h-4 text-cyan-400" />
              <span>
                AgentOps — Abyssal Intelligence v1.0.0 • Deep-Sea Autonomous Swarm Framework
              </span>
            </div>
            <div className="flex items-center gap-4 text-[11px]">
              <span className="text-teal-400/80">Cluster Alpha: Nominal</span>
              <span className="text-cyan-400/80">Latency: 14ms</span>
              <span className="text-slate-400">Realistic Demo Dataset</span>
            </div>
          </footer>
        </main>
      </div>
    </div>
  );
}
