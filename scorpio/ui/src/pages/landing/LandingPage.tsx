import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import type { SshSession } from "../../api/ssh/sshTypes";
import { useSshLogout } from "../../api/ssh/useSshLogout";
import {
  getSetupStatus,
  rebootHost,
  startInfrastructure,
  startSetup,
  stopInfrastructure,
  subscribeToDockerLogs,
  subscribeToSetup,
} from "../../api/setup/setupApi";
import type { DockerLog, SetupLog, SetupStatus } from "../../api/setup/setupTypes";
import { Brand } from "../../components/Brand/Brand";
import "./LandingPage.css";

type LandingPageProps = { session: SshSession; onDisconnected: () => void };

export function LandingPage({ session, onDisconnected }: LandingPageProps) {
  const navigate = useNavigate();
  const [setupStatus, setSetupStatus] = useState<SetupStatus | null>(null);
  const [logs, setLogs] = useState<SetupLog[]>([]);
  const [setupError, setSetupError] = useState<string | null>(null);
  const [isStarting, setIsStarting] = useState(false);
  const [dockerLogs, setDockerLogs] = useState<DockerLog[]>([]);
  const [infrastructureStatus, setInfrastructureStatus] = useState<"unknown" | "running" | "stopped">("unknown");
  const [infrastructureAction, setInfrastructureAction] = useState<"start" | "stop" | null>(null);
  const [sourceFilter] = useState<"all" | "setup" | "docker">("docker");
  const [serviceFilter, setServiceFilter] = useState("all");
  const [levelFilter, setLevelFilter] = useState("all");
  const [lastEventAt, setLastEventAt] = useState<number | null>(null);
  const [logPage, setLogPage] = useState(0);
  const { logout, isLoading, error } = useSshLogout(() => {
    onDisconnected();
    navigate("/login", { replace: true });
  });

  useEffect(() => {
    let active = true;

    getSetupStatus()
      .then((status) => {
        if (!active) return;
        setSetupStatus(status);
        setLogs(status.logs);
        setLastEventAt(Date.now());
      })
      .catch(() => setSetupError("No se pudo consultar el estado del setup."));

    const unsubscribe = subscribeToSetup((event) => {
      if (!active) return;

      if (event.type === "status") {
        setSetupStatus(event.data);
        setLogs(event.data.logs);
        setLastEventAt(Date.now());
      } else {
        setLogs((current) => [...current, event.data]);
        setLastEventAt(Date.now());
      }
    }, () => {
      if (active) setSetupError("Se perdió la conexión con los logs del setup.");
    });

    return () => {
      active = false;
      unsubscribe();
    };
  }, []);

  useEffect(() => {
    if (setupStatus?.status !== "completed") return undefined;

    const unsubscribe = subscribeToDockerLogs((event) => {
      setDockerLogs((current) => [...current, event.data]);
      setLastEventAt(Date.now());
    }, () => {
      setSetupError("Se perdió la conexión con los logs de la infraestructura.");
    });

    return unsubscribe;
  }, [setupStatus?.status]);

  async function handleSetup() {
    setIsStarting(true);
    setSetupError(null);

    try {
      await startSetup();
    } catch (error) {
      setSetupError(error instanceof Error ? error.message : "No se pudo iniciar el setup.");
    } finally {
      setIsStarting(false);
    }
  }

  async function handleInfrastructureAction(action: "start" | "stop") {
    setInfrastructureAction(action);
    setSetupError(null);

    try {
      if (action === "start") {
        await startInfrastructure();
        setInfrastructureStatus("running");
      } else {
        await stopInfrastructure();
        setInfrastructureStatus("stopped");
      }
    } catch (error) {
      setSetupError(error instanceof Error ? error.message : "No se pudo cambiar el estado de la infraestructura.");
    } finally {
      setInfrastructureAction(null);
    }
  }

  async function handleReboot() {
    if (!window.confirm("¿Estás seguro de que quieres reiniciar la Raspberry Pi?")) return;

    setSetupError(null);
    try {
      await rebootHost();
      setSetupError("La Raspberry Pi se está reiniciando. La conexión se cerrará temporalmente.");
    } catch (error) {
      setSetupError(error instanceof Error ? error.message : "No se pudo reiniciar la Raspberry Pi.");
    }
  }

  const progress = useMemo(() => {
    const latest = logs.at(-1);
    if (!latest?.step || !latest.total_steps) return null;
    return Math.round((latest.step / latest.total_steps) * 100);
  }, [logs]);

  const statusLabel = {
    idle: "Listo para instalar",
    running: "Instalación en progreso",
    completed: "Instalación completada",
    failed: "Instalación fallida",
  }[setupStatus?.status ?? "idle"];

  const services = Array.from(new Set(dockerLogs.map((log) => log.service))).sort();
  const levels = Array.from(new Set([
    ...logs.map((log) => log.level),
    ...dockerLogs.map((log) => log.level ?? ""),
  ].filter(Boolean))).sort();

  const visibleSetupLogs = logs.filter((log) => (
    (sourceFilter === "all" || sourceFilter === "setup") &&
    (levelFilter === "all" || log.level.toLowerCase() === levelFilter)
  ));

  const visibleDockerLogs = dockerLogs.filter((log) => (
    (sourceFilter === "all" || sourceFilter === "docker") &&
    (serviceFilter === "all" || log.service === serviceFilter) &&
    (levelFilter === "all" || (log.level ?? "").toLowerCase() === levelFilter)
  ));
  const logsPerPage = 10;
  const totalLogPages = Math.max(1, Math.ceil(visibleDockerLogs.length / logsPerPage));
  const pageStart = Math.max(0, visibleDockerLogs.length - (logPage + 1) * logsPerPage);
  const pageEnd = visibleDockerLogs.length - logPage * logsPerPage;
  const pageDockerLogs = visibleDockerLogs.slice(pageStart, pageEnd).reverse();

  return (
    <main className="landing-page">
      <header className="landing-header">
        <Brand />
        <div className="landing-header__actions">
          <span className="connection-status"><span aria-hidden="true" /> Conectado</span>
          <button className="text-button" type="button" onClick={logout} disabled={isLoading}>
            {isLoading ? "Desconectando…" : "Desconectar"}
          </button>
        </div>
      </header>

      <section className="landing-content" aria-labelledby="landing-title">
        <div className="landing-hero">
          <span className="eyebrow">ESTACIÓN CONECTADA</span>
          <h1 id="landing-title">Hola, <span>{session.username}</span>.</h1>
          <p>La conexión SSH está lista. Desde aquí podrás instalar y administrar Scorpio en tu Raspberry Pi.</p>
        </div>

        {error && <div className="landing-alert" role="alert">{error}</div>}

        <div className="landing-grid">
          <article className="connection-card">
            <div className="connection-card__icon" aria-hidden="true">⌁</div>
            <div>
              <span className="card-label">CONEXIÓN ACTIVA</span>
              <h2>{session.hostname}</h2>
              <p>Sesión iniciada como {session.username}</p>
            </div>
            <span className="connection-card__check" aria-label="Conexión correcta">✓</span>
          </article>

          <article className="setup-card">
            <div className="setup-card__header">
              <div>
                <span className="card-label">SCORPIO SETUP</span>
                <h2>{statusLabel}</h2>
              </div>
              <span className={`setup-status setup-status--${setupStatus?.status ?? "idle"}`}>
                {setupStatus?.status ?? "idle"}
              </span>
            </div>
            {progress !== null && <progress className="setup-progress" max="100" value={progress} />}
            <p>Instala las dependencias del host y prepara la infraestructura Docker.</p>
            {setupStatus?.completedAt && (
              <p className="setup-completed-at">
                Realizado el {new Date(setupStatus.completedAt).toLocaleString()}
              </p>
            )}
            {setupStatus?.status !== "completed" && (
              <button
                className="setup-button"
                type="button"
                onClick={handleSetup}
                disabled={isStarting || setupStatus?.status === "running"}
              >
                {isStarting || setupStatus?.status === "running" ? "Instalando…" : "Iniciar instalación"}
              </button>
            )}
            {setupStatus?.status === "completed" && (
              <div className="infrastructure-actions">
                <span className={`infrastructure-state infrastructure-state--${infrastructureStatus}`}>
                  Infraestructura: {infrastructureStatus === "running" ? "activa" : infrastructureStatus === "stopped" ? "detenida" : "sin consultar"}
                </span>
                <button
                  className="setup-button setup-button--secondary"
                  type="button"
                  onClick={() => handleInfrastructureAction("start")}
                  disabled={infrastructureAction !== null || infrastructureStatus === "running"}
                >
                  {infrastructureAction === "start" ? "Iniciando…" : "Start"}
                </button>
                <button
                  className="setup-button setup-button--danger"
                  type="button"
                  onClick={() => handleInfrastructureAction("stop")}
                  disabled={infrastructureAction !== null || infrastructureStatus === "stopped"}
                >
                  {infrastructureAction === "stop" ? "Deteniendo…" : "Stop"}
                </button>
              </div>
            )}
          </article>
        </div>

        {setupError && <div className="landing-alert" role="alert">{setupError}</div>}

        {setupStatus?.status !== "completed" && <section className="logs-panel" aria-labelledby="logs-title">
          <div className="logs-panel__header">
            <div>
              <span className="card-label">ACTIVIDAD EN VIVO</span>
              <h2 id="logs-title">Logs de instalación</h2>
            </div>
            <div className="logs-panel__tools">
              <span className="logs-count">{visibleSetupLogs.length} eventos</span>
              <button className="refresh-button" type="button" onClick={() => window.location.reload()}>
                Recargar
              </button>
            </div>
          </div>
          {lastEventAt && <span className="logs-updated">Actualizado {new Date(lastEventAt).toLocaleTimeString()}</span>}
          <div className="logs-table-header" aria-hidden="true">
            <span>Fuente</span><span>Fecha / hora</span><span>Nivel</span><span>Capa</span><span>Registro</span>
          </div>
          <div className="logs-terminal" role="log" aria-live="polite">
            {visibleSetupLogs.length === 0 ? (
              <p className="logs-empty">Los eventos de instalación aparecerán aquí.</p>
            ) : visibleSetupLogs.map((log, index) => (
              <div className="log-line" key={`${log.timestamp}-${index}`}>
                <span className="log-service">{log.module}</span>
                <span className="log-separator">|</span>
                <time dateTime={log.timestamp}>{new Date(log.timestamp).toLocaleTimeString()}</time>
                <span className="log-separator">|</span>
                <span className={`log-level log-level--${log.level}`}>{log.level.toUpperCase()}</span>
                <span className="log-separator">|</span>
                <span className="log-layer">{log.step_id ?? "setup"}</span>
                <span className="log-separator">|</span>
                <span className="log-message">{log.message}</span>
              </div>
            ))}
          </div>
        </section>}

        {setupStatus?.status === "completed" && (
          <section className="logs-panel" aria-labelledby="docker-logs-title">
            <div className="logs-panel__header">
              <div>
                <span className="card-label">INFRAESTRUCTURA EN VIVO</span>
                <h2 id="docker-logs-title">Logs de servicios</h2>
              </div>
              <span className="logs-count">{visibleDockerLogs.length} eventos</span>
            </div>
          <div className="logs-filters logs-filters--services" aria-label="Filtro de servicios">
              <label>Servicio
              <select value={serviceFilter} onChange={(event) => { setServiceFilter(event.target.value); setLogPage(0); }}>
                  <option value="all">Todos</option>
                {services.map((service) => <option key={service} value={service}>{service}</option>)}
              </select>
            </label>
              {lastEventAt && <span className="logs-updated">Actualizado {new Date(lastEventAt).toLocaleTimeString()}</span>}
          </div>
          <div className="logs-pagination" aria-label="Paginación de logs">
            <button type="button" disabled={logPage === totalLogPages - 1} onClick={() => setLogPage((page) => page + 1)}>
              Anteriores
            </button>
            <span>Página {logPage + 1} de {totalLogPages}</span>
            <button type="button" disabled={logPage === 0} onClick={() => setLogPage((page) => page - 1)}>
              Siguientes
            </button>
          </div>
            <div className="logs-table-header" aria-hidden="true">
              <span>Servicio</span><span>Fecha / hora</span><span>Nivel</span><span>Capa</span><span>Registro</span>
            </div>
            <div className="logs-terminal" role="log" aria-live="polite">
              {pageDockerLogs.length === 0 ? (
                <p className="logs-empty">Los logs de Docker aparecerán aquí.</p>
              ) : pageDockerLogs.map((log, index) => (
                <div className="log-line" key={`${log.timestamp}-${index}`}>
                  <span className="log-service">{log.service}</span>
                  <span className="log-separator">|</span>
                  <time dateTime={log.timestamp ?? undefined}>{log.timestamp ?? "--"}</time>
                  <span className="log-separator">|</span>
                  <span className={`log-level log-level--${(log.level ?? "info").toLowerCase()}`}>
                    {(log.level ?? "INFO").toUpperCase()}
                  </span>
                  <span className="log-separator">|</span>
                  <span className="log-layer">{log.layer ?? "service"}</span>
                  <span className="log-separator">|</span>
                  <span className="log-message">{log.message}</span>
                </div>
              ))}
            </div>
          </section>
        )}
        {setupStatus?.status === "completed" && (
          <button className="reboot-button" type="button" onClick={handleReboot}>
            Reiniciar Raspberry Pi
          </button>
        )}
      </section>
    </main>
  );
}
