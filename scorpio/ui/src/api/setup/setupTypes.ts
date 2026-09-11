export type SetupLog = {
  level: string;
  module: string;
  step: number | null;
  total_steps: number | null;
  step_id: string | null;
  message: string;
  timestamp: string;
};

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
  services: InfrastructureService[];
};

export type SetupEvent =
  | { type: "status"; data: SetupStatus }
  | { type: "log"; data: SetupLog };

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
