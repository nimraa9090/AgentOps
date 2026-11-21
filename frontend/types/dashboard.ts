export type OperationalDepth = "Epipelagic" | "Mesopelagic" | "Bathypelagic" | "Abyssopelagic" | "Hadopelagic";

export type AgentStatus = "active" | "idle" | "computing" | "degraded";

export type ExecutionStatus = "completed" | "running" | "failed" | "degraded";

export interface MetricCardData {
  id: string;
  title: string;
  value: string;
  change: string;
  isPositive: boolean;
  metricLabel: string;
  description: string;
  depthTag: string;
  iconName: "Activity" | "Cpu" | "Zap" | "ShieldCheck" | "Database" | "Coins";
}

export interface ExecutionActivityPoint {
  time: string;
  totalExecutions: number;
  successful: number;
  retried: number;
  failed: number;
  latencyMs: number;
}

export interface AgentPerformanceMetric {
  agentName: string;
  model: string;
  avgLatencyMs: number;
  tokensPerSec: number;
  successRate: number;
  costEfficiency: number;
}

export interface AgentInfo {
  id: string;
  name: string;
  codenamedDepth: string;
  role: string;
  model: string;
  status: AgentStatus;
  currentTask: string;
  operationalDepthMeters: number;
  memoryUsageMb: number;
  tokensProcessed: number;
  avgLatencyMs: number;
  successRatePercent: number;
  uptimeHours: number;
}

export interface ExecutionTrace {
  id: string;
  agentId: string;
  agentName: string;
  triggerType: "API Webhook" | "Scheduled Cron" | "Swarm Event" | "Human Prompt" | "Autonomous Goal";
  modelUsed: string;
  status: ExecutionStatus;
  tokensConsumed: number;
  costEstimateUsd: number;
  latencyMs: number;
  timestamp: string;
  stepCount: number;
  depthZone: OperationalDepth;
}

export interface SystemHealthItem {
  id: string;
  name: string;
  category: "Gateway" | "Vector Lake" | "Swarm Bus" | "LLM Circuit" | "Telemetry Stream";
  status: "optimal" | "nominal" | "warning";
  value: string;
  latencyMs: number;
  depthZone: OperationalDepth;
  details: string;
}
