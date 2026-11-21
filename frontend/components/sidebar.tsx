"use client";

import React from "react";
import {
  LayoutDashboard,
  Bot,
  Route,
  Activity,
  Layers,
  ShieldAlert,
  Server,
  Sliders,
  Compass,
  Radio,
  ChevronRight,
  Waves,
  X,
  ExternalLink,
} from "lucide-react";

interface SidebarProps {
  activeSection: string;
  onSelectSection: (section: string) => void;
  mobileOpen: boolean;
  onCloseMobile: () => void;
}

interface NavItem {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
  depthTag?: string;
}

const NAV_GROUPS: { group: string; items: NavItem[] }[] = [
  {
    group: "Command Center",
    items: [
      { id: "overview", label: "Overview Telemetry", icon: LayoutDashboard },
      { id: "swarms", label: "Agent Swarms", icon: Bot, badge: "42 Active" },
      { id: "traces", label: "Execution Traces", icon: Route },
      { id: "sonar", label: "Sonar Analytics", icon: Activity },
    ],
  },
  {
    group: "Abyssal Intelligence",
    items: [
      { id: "memory", label: "Vector Ocean RAG", icon: Layers, depthTag: "3,800m" },
      { id: "guardrails", label: "Trench Guardrails", icon: ShieldAlert },
      { id: "clusters", label: "Subsea Clusters", icon: Server, badge: "2 Alpha" },
    ],
  },
  {
    group: "Configuration",
    items: [
      { id: "settings", label: "Telemetry & Keys", icon: Sliders },
    ],
  },
];

export function Sidebar({
  activeSection,
  onSelectSection,
  mobileOpen,
  onCloseMobile,
}: SidebarProps) {
  return (
    <>
      {/* Mobile Backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/70 backdrop-blur-sm lg:hidden transition-opacity"
          onClick={onCloseMobile}
        />
      )}

      {/* Main Sidebar */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 w-72 flex flex-col bg-[#040816]/95 border-r border-cyan-900/30 backdrop-blur-xl transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Branding Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-cyan-950/60">
          <div className="flex items-center gap-3">
            <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500/20 via-teal-500/10 to-blue-900/40 border border-cyan-400/40 shadow-[0_0_15px_rgba(6,182,212,0.25)]">
              <Compass className="w-5 h-5 text-cyan-300 animate-spin-slow" />
              <div className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-teal-400 border-2 border-[#040816]" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-base tracking-tight text-white glow-cyan">
                  AgentOps
                </span>
                <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800/50">
                  v1.0
                </span>
              </div>
              <p className="text-[11px] font-mono text-cyan-400/70 tracking-wider flex items-center gap-1">
                <Waves className="w-3 h-3 text-teal-400" />
                Abyssal Intelligence
              </p>
            </div>
          </div>

          <button
            onClick={onCloseMobile}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 lg:hidden"
            aria-label="Close sidebar"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Ocean Depth Indicator Banner */}
        <div className="mx-4 my-3 p-3 rounded-lg bg-gradient-to-r from-blue-950/40 via-cyan-950/20 to-slate-900/40 border border-cyan-500/15">
          <div className="flex items-center justify-between text-[11px] text-cyan-300 font-mono mb-1">
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-pulse"></span>
              Zone: Hadopelagic
            </span>
            <span className="text-slate-400">10,920m</span>
          </div>
          <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden">
            <div
              className="bg-gradient-to-r from-teal-400 to-cyan-400 h-1.5 rounded-full shadow-[0_0_8px_rgba(6,182,212,0.6)]"
              style={{ width: "88%" }}
            />
          </div>
          <div className="flex justify-between text-[9px] text-slate-500 font-mono mt-1">
            <span>Surface</span>
            <span>Challenger Deep</span>
          </div>
        </div>

        {/* Navigation Sections */}
        <div className="flex-1 overflow-y-auto px-3 py-2 space-y-6">
          {NAV_GROUPS.map((group) => (
            <div key={group.group}>
              <h3 className="px-3 mb-2 text-[10px] font-mono font-semibold uppercase tracking-wider text-cyan-400/60">
                {group.group}
              </h3>
              <nav className="space-y-1">
                {group.items.map((item) => {
                  const Icon = item.icon;
                  const isActive = activeSection === item.id;
                  return (
                    <button
                      key={item.id}
                      onClick={() => {
                        onSelectSection(item.id);
                        onCloseMobile();
                      }}
                      className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-all group ${
                        isActive
                          ? "bg-gradient-to-r from-cyan-950/70 to-blue-950/40 text-cyan-200 border border-cyan-500/30 shadow-[0_0_12px_rgba(6,182,212,0.15)]"
                          : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 hover:border hover:border-slate-700/50"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <Icon
                          className={`w-4 h-4 transition-colors ${
                            isActive
                              ? "text-cyan-400 glow-cyan"
                              : "text-slate-500 group-hover:text-cyan-400"
                          }`}
                        />
                        <span>{item.label}</span>
                      </div>

                      <div className="flex items-center gap-1.5">
                        {item.badge && (
                          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-full bg-cyan-900/60 text-cyan-300 border border-cyan-700/40">
                            {item.badge}
                          </span>
                        )}
                        {item.depthTag && (
                          <span className="text-[9px] font-mono text-slate-500">
                            {item.depthTag}
                          </span>
                        )}
                        {isActive && (
                          <ChevronRight className="w-3.5 h-3.5 text-cyan-400" />
                        )}
                      </div>
                    </button>
                  );
                })}
              </nav>
            </div>
          ))}
        </div>

        {/* Subsea Cluster Status Footer */}
        <div className="p-4 border-t border-cyan-950/70 bg-[#030612]/90">
          <div className="p-3 rounded-lg bg-[#071024] border border-cyan-500/15 text-xs">
            <div className="flex items-center justify-between mb-2">
              <span className="flex items-center gap-2 text-slate-300 font-medium">
                <Radio className="w-3.5 h-3.5 text-teal-400 animate-pulse" />
                Cluster Alpha (Sim)
              </span>
              <span className="text-[10px] font-mono text-teal-400 bg-teal-950/60 px-1.5 py-0.5 rounded border border-teal-800/40">
                14 ms
              </span>
            </div>
            <div className="flex items-center justify-between text-[11px] text-slate-400 font-mono">
              <span>Swarm Load:</span>
              <span className="text-cyan-300">42 / 48 nodes</span>
            </div>
            <div className="mt-2 pt-2 border-t border-slate-800/60 flex items-center justify-between text-[10px] text-slate-500 font-mono">
              <span>Sonar Frequency: 44.1 kHz</span>
              <span className="text-cyan-400/80">Simulated</span>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
