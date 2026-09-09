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
  lastLog: SetupLog | null;
  logs: SetupLog[];
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
