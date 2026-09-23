/** Installation step emitted by setup; timestamp is an ISO date string. */
export type SetupLog = {
  level: string;
  module: string;
  step: number | null;
  total_steps: number | null;
  step_id: string | null;
  message: string;
  timestamp: string;
};

/** Existing wire format; casing follows the backend rather than UI conventions. */
export type SetupStatus = {
  status: "idle" | "running" | "completed" | "failed";
  error: string | null;
  startedAt: string | null;
  finishedAt: string | null;
  completedAt?: string | null;
  timezone?: string | null;
  version?: Record<string, string> | null;
  lastLog: SetupLog | null;
  logs: SetupLog[];
  ssh_active: boolean;
  infrastructure: InfrastructureStatus;
};

export type InfrastructureService = {
  name: string | null;
  state: string;
  status: string;
};

export type InfrastructureStatus = {
  status: "running" | "stopped";
  /** The setup status endpoint currently returns only status. */
  services?: InfrastructureService[];
};

/** Discriminated SSE messages: full state or a single appended log. */
export type SetupEvent = { type: "status"; data: SetupStatus } | { type: "log"; data: SetupLog };

/** Docker log fields may be unavailable when parsing raw command output. */
export type DockerLog = {
  service: string;
  timestamp: string | null;
  level: string | null;
  layer: string | null;
  message: string;
};

export type DockerLogEvent = {
  type: "log";
  source: "docker";
  data: DockerLog;
};

/** Accepted setup request; this acknowledges start, not completion. */
export type StartSetupResponse = { status: "running"; message: string };
