import { useDashboard } from "../hooks/useDashboard";
import { useLogFilters } from "../hooks/useLogFilters";
import { SetupCard } from "./SetupCard";
import InfrastructureCard from "./InfrastructureCard";
import { ServiceLogsPanel } from "./ServiceLogsPanel";
import { LogTable } from "./LogTable";
import "../styles/dashboard.css";

export default function Dashboard() {
  const dashboard = useDashboard();
  const filters = useLogFilters(dashboard.dockerLogs);
  const { error, setupState, status, setStatus, setError, setupLogs, reboot } = dashboard;
  return (
    <>
      {error && (
        <div className="landing-alert" role="alert">
          {error}
        </div>
      )}
      <div className="landing-grid">
        <SetupCard {...dashboard} />
        <InfrastructureCard
          setupState={setupState}
          status={status}
          setStatus={setStatus}
          setError={setError}
        />
      </div>
      {setupState !== "completed" && <LogTable title="Installation logs" logs={setupLogs} />}
      {setupState === "completed" && <ServiceLogsPanel filters={filters} />}
      {setupState === "completed" && (
        <button className="reboot-button" type="button" onClick={reboot}>
          Reboot Raspberry Pi
        </button>
      )}
    </>
  );
}
