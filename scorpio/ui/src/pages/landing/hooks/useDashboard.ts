import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getSetupStatus, startSetup, subscribeToSetup } from "../../../api/setup/setupApi";
import { rebootHost } from "../../../api/infrastructure/infrastructureApi";
import { subscribeToDockerLogs } from "../../../api/logs/logsApi";
import type { DockerLog, SetupLog, SetupStatus } from "../../../api/setup/setupTypes";
import { clearSshSession } from "../../../helpers/sshSessionStorage";

/** Own the dashboard requests, subscriptions, and installation/reboot actions. */
export function useDashboard() {
  const navigate = useNavigate();
  const [status, setStatus] = useState<SetupStatus | null>(null);
  const [setupLogs, setSetupLogs] = useState<SetupLog[]>([]);
  const [dockerLogs, setDockerLogs] = useState<DockerLog[]>([]);
  const [error, setError] = useState<string | null>(null);

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
    getSetupStatus()
      .then((value) => {
        if (active) {
          if (!value.ssh_active) {
            redirectToLogin();
            return;
          }
          setStatus(value);
          setSetupLogs(value.logs);
        }
      })
      .catch(() => setError("Could not retrieve the setup status."));
    const unsubscribe = subscribeToSetup(
      (event) => {
        if (!active) return;
        if (event.type === "status") {
          setStatus(event.data);
          setSetupLogs(event.data.logs);
        } else setSetupLogs((current) => [...current, event.data]);
      },
      () => {
        if (!active) return;
        void handleConnectionError("The connection to the setup logs was temporarily lost.");
      },
    );
    return () => {
      active = false;
      unsubscribe();
    };
  }, []);

  useEffect(() => {
    // Start the Docker log stream only after setup is complete.
    if (status?.status !== "completed") return undefined;
    const unsubscribe = subscribeToDockerLogs(
      (event) => setDockerLogs((current) => [...current, event.data]),
      () => {
        void handleConnectionError("The connection to the Docker logs was temporarily lost.");
      },
    );
    return unsubscribe;
  }, [status?.status]);

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
      setError(reason instanceof Error ? reason.message : "Could not reboot the Raspberry Pi.");
    }
  }

  const log = setupLogs.at(-1);
  const progress =
    log?.step && log.total_steps ? Math.round((log.step / log.total_steps) * 100) : null;
  return {
    status,
    setStatus,
    setupLogs,
    dockerLogs,
    error,
    setError,
    progress,
    setupState: status?.status ?? "idle",
    setup,
    reboot,
  };
}
