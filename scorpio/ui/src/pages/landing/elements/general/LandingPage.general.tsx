import { useEffect, useMemo, useState } from "react";
import type { CSSProperties } from "react";
import { useNavigate } from "react-router-dom";
import {
  getSetupStatus,
  rebootHost, startSetup, subscribeToDockerLogs, subscribeToSetup
} from "../../../../api/setup/setupApi";
import type { DockerLog, SetupLog, SetupStatus } from "../../../../api/setup/setupTypes";
import { clearSshSession } from "../../../../helpers/sshSessionStorage";
import LandingPageStatus from "../status/LandingPageStatus";
import "./LandingPage.general.css";

const labels = {
  idle: "Ready to install",
  running: "Installation in progress",
  completed: "Installation complete",
  failed: "Installation failed"
} as const;

const timeRanges = {
  all: { label: "All time", milliseconds: null },
  "15m": { label: "Last 15 minutes", milliseconds: 15 * 60 * 1000 },
  "1h": { label: "Last hour", milliseconds: 60 * 60 * 1000 },
  "24h": { label: "Last 24 hours", milliseconds: 24 * 60 * 60 * 1000 },
  "7d": { label: "Last 7 days", milliseconds: 7 * 24 * 60 * 60 * 1000 },
  "30d": { label: "Last month", milliseconds: 30 * 24 * 60 * 60 * 1000 },
} as const;

type TimeRange = keyof typeof timeRanges;

export default function LandingPageGeneral() {
  // Coordinate setup state, infrastructure actions, and live logs.
  const navigate = useNavigate();
  const [status, setStatus] = useState<SetupStatus | null>(null);
  const [setupLogs, setSetupLogs] = useState<SetupLog[]>([]);
  const [dockerLogs, setDockerLogs] = useState<DockerLog[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [service, setService] = useState("all");
  const [timeRange, setTimeRange] = useState<TimeRange>("1h");
  const [filterNow, setFilterNow] = useState(Date.now());

  function redirectToLogin() {
    clearSshSession();
    navigate("/login", { replace: true });
  }

  async function handleConnectionError(message: string) {
    try {
      const currentStatus = await getSetupStatus();
      if (!currentStatus.ssh_active) {
        redirectToLogin();
        return;
      }
    } catch {
      // Keep the dashboard open when the status check is inconclusive.
    }

    setError(message);
  }

  useEffect(() => {
    // Load persisted setup data and listen for setup updates.
    let active = true;
    getSetupStatus().then((value) => {
      if (active) {
        if (!value.ssh_active) {
          redirectToLogin();
          return;
        }
        setStatus(value);
        setSetupLogs(value.logs);
      }
    }).catch(() => setError("Could not retrieve the setup status."));
    const unsubscribe = subscribeToSetup((event) => {
      if (!active) return;
      if (event.type === "status") {
        setStatus(event.data);
        setSetupLogs(event.data.logs);
      } else setSetupLogs((current) => [...current, event.data]);
    }, () => {
      if (!active) return;
      void handleConnectionError("The connection to the setup logs was temporarily lost.");
    });
    return () => {
      active = false;
      unsubscribe();
    };
  }, []);

  useEffect(() => {
    // Start the Docker log stream only after setup is complete.
    if (status?.status !== "completed") return undefined;
    const unsubscribe = subscribeToDockerLogs((event) => setDockerLogs(
      (current) => [...current, event.data]),
      () => {
        void handleConnectionError("The connection to the Docker logs was temporarily lost.");
      });
    return unsubscribe;
  }, [status?.status]);

  useEffect(() => {
    if (timeRange === "all") return undefined;
    const interval = window.setInterval(() => setFilterNow(Date.now()), 30_000);
    return () => window.clearInterval(interval);
  }, [timeRange]);

  const visibleLogs = useMemo(() => {
    const range = timeRanges[timeRange].milliseconds;
    const cutoff = range === null ? null : filterNow - range;

    return dockerLogs
      .filter((log) => service === "all" || log.service === service)
      .filter((log) => {
        if (cutoff === null) return true;
        if (!log.timestamp) return false;
        const timestamp = Date.parse(log.timestamp);
        return Number.isFinite(timestamp) && timestamp >= cutoff;
      })
      .sort((left, right) => {
        const leftTime = left.timestamp ? Date.parse(left.timestamp) : 0;
        const rightTime = right.timestamp ? Date.parse(right.timestamp) : 0;
        return rightTime - leftTime;
      });
  }, [dockerLogs, filterNow, service, timeRange]);

  const services = Array.from(new Set(dockerLogs.map((log) => log.service))).sort();
  const serviceColorByName = useMemo(() => Object.fromEntries(
    services.map((name, index) => [
      name,
      `hsl(${Math.round((index * 137.508 + 32) % 360)} 68% 46%)`,
    ]),
  ), [services]);
  const progress = useMemo(() => {
    const log = setupLogs.at(-1);
    return log?.step && log.total_steps
      ? Math.round(log.step / log.total_steps * 100)
      : null;
  },
    [setupLogs]);
  const setupState = status?.status ?? "idle";

  async function setup() {
    // Start setup and let the SSE stream update its progress.
    try {
      await startSetup();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not start the setup process.");
    }
  }
  async function reboot() {
    // Confirm the destructive action before rebooting the host.
    if (!window.confirm("Are you sure you want to reboot the Raspberry Pi?")) return;
    try {
      await rebootHost();
      setError("The Raspberry Pi is rebooting.");
    } catch (reason) {
      setError(reason instanceof Error
        ? reason.message
        : "Could not reboot the Raspberry Pi.");
    }
  }

  return <>
    {error && <div className="landing-alert" role="alert">{error}</div>}
    {/* Card for installation status */}
    <div className="landing-grid">
      <article className="setup-card">
        <div className="setup-card__header">
          <div>
            <span className="card-label">General</span>
            <h2>{labels[setupState]}</h2>
          </div>
          <span className={`setup-status setup-status--${setupState}`}>{setupState}</span>
        </div>
        {progress !== null &&
          <progress className="setup-progress" max="100" value={progress} />}
        {status?.completedAt &&
          <p className="setup-completed-at">
            Completed on {new Date(status.completedAt).toLocaleString("en-US")}
          </p>}
        {setupState !== "completed" &&
          <>
            <p>
              <span className="setup-warning">⚠️</span>
              Before starting the installation, make sure your Raspberry Pi is connected to the internet and has enough free space.
              The installation process may take several minutes.
            </p>
            <button
              className="setup-button"
              type="button"
              onClick={setup}
              disabled={setupState === "running"}>
              Start installation
            </button>
          </>
        }
      </article>
      <LandingPageStatus
        setupState={setupState}
        status={status}
        setStatus={setStatus}
        setError={setError}
      />
    </div>

    {setupState !== "completed" && <LogTable title="Installation logs" logs={setupLogs} />}
    {/* Logs for live status */}
    {setupState === "completed" &&
      <section className="logs-panel">
        <div className="logs-panel__header">
          <div>
            <h2>Service logs</h2>
            <span className="card-label">LIVE INFRASTRUCTURE</span>
          </div>
          <span className="logs-count">{visibleLogs.length} events</span>
        </div>
        <div className="logs-filters logs-filters--services">
          <label>Service
            <select value={service} onChange={(event) => setService(event.target.value)}>
              <option value="all">All</option>
              {services.map((item) => <option key={item}>{item}</option>)}
            </select>
          </label>
          <label>Time range
            <select
              value={timeRange}
              onChange={(event) => setTimeRange(event.target.value as TimeRange)}>
              {Object.entries(timeRanges).map(([value, range]) =>
                <option key={value} value={value}>{range.label}</option>)}
            </select>
          </label>
        </div>
        <LogRows logs={visibleLogs} service sourceColors={serviceColorByName} />
      </section>}
    {setupState === "completed" &&
      <button className="reboot-button" type="button" onClick={reboot}>
        Reboot Raspberry Pi
      </button>}
  </>;
}

function LogTable({ title, logs }: { title: string; logs: SetupLog[] }) {
  // Render the setup event table.
  return (
    <section className="logs-panel"><div className="logs-panel__header">
      <div>
        <span className="card-label">LIVE ACTIVITY</span>
        <h2>{title}</h2>
      </div>
      <span className="logs-count">{logs.length} events</span>
    </div><LogRows logs={logs} />
    </section>
  )
}

type LogRowsProps = {
  logs: Array<SetupLog | DockerLog>;
  service?: boolean;
  sourceColors?: Record<string, string>;
};

function LogRows({ logs, service = false, sourceColors = {} }: LogRowsProps) {
  // Render normalized setup or Docker events as table rows.
  const [expandedLog, setExpandedLog] = useState<number | null>(null);
  const orderedLogs = useMemo(() => [...logs].sort((left, right) => {
    const leftTime = left.timestamp ? Date.parse(left.timestamp) : 0;
    const rightTime = right.timestamp ? Date.parse(right.timestamp) : 0;
    return rightTime - leftTime;
  }), [logs]);

  return <div className="logs-table">
    <div className="logs-terminal" role="log" aria-live="polite">
      <div className="logs-table-header">
        <span>{service ? "Service" : "Source"}</span>
        <span>Date / time</span>
        <span>Level</span>
        <span>Layer</span>
        <span>Message</span>
        <span className="visually-hidden">Actions</span>
      </div>
      {orderedLogs.length === 0
        ? <p className="logs-empty">No events to display.</p>
        : orderedLogs.map((log, index) => {
          const docker = "service" in log;
          const timestamp = log.timestamp ?? new Date().toISOString();
          const level = log.level ?? "info";
          const isExpanded = expandedLog === index;
          const source = docker ? log.service : log.module;
          const rowStyle = {
            "--service-color": sourceColors[source] ?? getServiceColor(source),
          } as CSSProperties;
          return <div
            className={`log-line log-line--${level.toLowerCase()}`}
            key={`${timestamp}-${source}-${index}`}
            style={rowStyle}>
            <span className="log-service">{source}</span>
            <time>{new Date(timestamp).toLocaleString("en-US")}</time>
            <span className={`log-level log-level--${level.toLowerCase()}`}>{level.toUpperCase()}</span>
            <span className="log-layer">{docker ? log.layer ?? "service" : log.step_id ?? "setup"}</span>
            <span className="log-message" title={log.message}>{log.message}</span>
            <button
              className="log-detail-btn"
              type="button"
              aria-label={`${isExpanded ? "Hide" : "Show"} details for event ${index + 1}`}
              aria-expanded={isExpanded}
              onClick={() => setExpandedLog(isExpanded ? null : index)}
              >
              {isExpanded ? "-" : "+"}
            </button>
            {isExpanded && <div className="log-detail-row"><LogRowDetail log={log} /></div>}

          </div>;
        })}
    </div>
  </div>;
}

const serviceColors = [
  "#ec9f24",
  "#4f7ee8",
  "#a45ee5",
  "#18a47b",
  "#df5c78",
  "#3a9db8",
  "#bf6b32",
  "#6c70d9",
];

function getServiceColor(service: string): string {
  let hash = 0;
  for (const character of service) {
    hash = ((hash << 5) - hash + character.charCodeAt(0)) | 0;
  }
  return serviceColors[(hash >>> 0) % serviceColors.length];
}

function LogRowDetail({ log }: { log: SetupLog | DockerLog }) {
  // Render a detailed view of a single log entry.
  const docker = "service" in log;
  const timestamp = log.timestamp ?? new Date().toISOString();
  const level = log.level ?? "info";
  return <div className="log-detail-card">
    <div><strong>Source:</strong> {docker ? log.service : log.module}</div>
    <div><strong>Date / time:</strong> {new Date(timestamp).toLocaleString("en-US")}</div>
    <div><strong>Level:</strong> {level.toUpperCase()}</div>
    <div><strong>Layer:</strong> {docker ? log.layer ?? "service" : log.step_id ?? "setup"}</div>
    <div><strong>Message:</strong> {log.message}</div>
  </div>;
}
