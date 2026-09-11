import { useEffect, useMemo, useState } from "react";
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
  idle: "Listo para instalar",
  running: "Instalación en progreso",
  completed: "Instalación completada",
  failed: "Instalación fallida"
} as const;

export default function LandingPageGeneral() {
  // Coordinate setup state, infrastructure actions, and live logs.
  const navigate = useNavigate();
  const [status, setStatus] = useState<SetupStatus | null>(null);
  const [setupLogs, setSetupLogs] = useState<SetupLog[]>([]);
  const [dockerLogs, setDockerLogs] = useState<DockerLog[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [service, setService] = useState("all");
  const [page, setPage] = useState(0);

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
    }).catch(() => setError("No se pudo consultar el estado del setup."));
    const unsubscribe = subscribeToSetup((event) => {
      if (!active) return;
      if (event.type === "status") {
        setStatus(event.data);
        setSetupLogs(event.data.logs);
      } else setSetupLogs((current) => [...current, event.data]);
    }, () => {
      if (!active) return;
      void handleConnectionError("Se perdió temporalmente la conexión con los logs del setup.");
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
        void handleConnectionError("Se perdió temporalmente la conexión con los logs Docker.");
      });
    return unsubscribe;
  }, [status?.status]);

  const visibleLogs = dockerLogs
    .filter((log) => service === "all" || log.service === service)
    .sort((left, right) => {
      const leftTime = left.timestamp ? Date.parse(left.timestamp) : 0;
      const rightTime = right.timestamp ? Date.parse(right.timestamp) : 0;
      return leftTime - rightTime;
    });
  const pages = Math.max(1, Math.ceil(visibleLogs.length / 10));
  const currentLogs = visibleLogs.slice(
    Math.max(0, visibleLogs.length - (page + 1) * 10),
    visibleLogs.length - page * 10).reverse();

    
  const services = Array.from(new Set(dockerLogs.map((log) => log.service))).sort();
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
      setError(reason instanceof Error ? reason.message : "No se pudo iniciar el setup.");
    }
  }
  async function reboot() {
    // Confirm the destructive action before rebooting the host.
    if (!window.confirm("¿Estás seguro de que quieres reiniciar la Raspberry Pi?")) return;
    try {
      await rebootHost();
      setError("La Raspberry Pi se está reiniciando.");
    } catch (reason) {
      setError(reason instanceof Error
        ? reason.message
        : "No se pudo reiniciar la Raspberry Pi.");
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
            Realizado el {new Date(status.completedAt).toLocaleString()}
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
              Iniciar instalación
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

    {setupState !== "completed" && <LogTable title="Logs de instalación" logs={setupLogs} />}
    {/* Logs for live status */}
    {setupState === "completed" &&
      <section className="logs-panel">
        <div className="logs-panel__header">
          <div>
            <span className="card-label">INFRAESTRUCTURA EN VIVO</span>
            <h2>Logs de servicios</h2>
          </div>
          <span className="logs-count">{visibleLogs.length} eventos</span>
        </div>
        <div className="logs-filters logs-filters--services">
          <label>Servicio
            <select value={service} onChange={(event) => { setService(event.target.value); setPage(0); }}>
              <option value="all">Todos</option>
              {services.map((item) => <option key={item}>{item}</option>)}
            </select>
          </label>
        </div>
        <div className="logs-pagination">
          <button type="button" disabled={page === pages - 1} onClick={() => setPage((value) => value + 1)}>
            Anteriores
          </button>
          <span>Página {page + 1} de {pages}</span>
          <button type="button" disabled={page === 0} onClick={() => setPage((value) => value - 1)}>
            Siguientes
          </button>
        </div>
        <LogRows logs={currentLogs} service />
      </section>}
    {setupState === "completed" &&
      <button className="reboot-button" type="button" onClick={reboot}>
        Reiniciar Raspberry Pi
      </button>}
  </>;
}

function LogTable({ title, logs }: { title: string; logs: SetupLog[] }) {
  // Render the setup event table.
  return (
    <section className="logs-panel"><div className="logs-panel__header">
      <div>
        <span className="card-label">ACTIVIDAD EN VIVO</span>
        <h2>{title}</h2>
      </div>
      <span className="logs-count">{logs.length} eventos</span>
    </div><LogRows logs={logs} />
    </section>
  )
}

function LogRows({ logs, service = false }: { logs: Array<SetupLog | DockerLog>; service?: boolean }) {
  // Render normalized setup or Docker events as table rows.
  return <>
    <div className="logs-table-header">
      <span>{service ? "Servicio" : "Fuente"}</span>
      <span>Fecha / hora</span>
      <span>Nivel</span>
      <span>Capa</span>
      <span>Registro</span>
    </div>
    <div className="logs-terminal" role="log" aria-live="polite">
      {logs.length === 0
        ? <p className="logs-empty">No hay eventos para mostrar.</p>
        : logs.map((log, index) => {
          const docker = "service" in log;
          const timestamp = log.timestamp ?? new Date().toISOString();
          const level = log.level ?? "info";
          return <div className="log-line" key={`${timestamp}-${index}`}>
            <span className="log-service">{docker ? log.service : log.module}</span>
            <time>{new Date(timestamp).toLocaleString()}</time>
            <span className={`log-level log-level--${level.toLowerCase()}`}>{level.toUpperCase()}</span>
            <span className="log-layer">{docker ? log.layer ?? "service" : log.step_id ?? "setup"}</span>
            <span className="log-message">{log.message}</span>
          </div>;
        })}
    </div>
  </>;
}
