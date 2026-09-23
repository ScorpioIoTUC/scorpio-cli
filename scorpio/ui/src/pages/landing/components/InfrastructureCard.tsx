import { useState } from "react";
import { GrUpdate } from "react-icons/gr";

import type { Dispatch, SetStateAction } from "react";

import {
  startInfrastructure,
  stopInfrastructure,
} from "../../../api/infrastructure/infrastructureApi";
import type { SetupStatus } from "../../../api/setup/setupTypes";

type InfrastructureCardProps = {
  setupState: SetupStatus["status"];
  status: SetupStatus | null;
  setStatus: Dispatch<SetStateAction<SetupStatus | null>>;
  setError: Dispatch<SetStateAction<string | null>>;
};

export default function InfrastructureCard({
  setupState,
  status,
  setStatus,
  setError,
}: InfrastructureCardProps) {
  const [action, setAction] = useState<"start" | "stop" | null>(null);
  const infrastructureStatus = status?.infrastructure.status ?? "stopped";

  async function infrastructure(next: "start" | "stop") {
    setAction(next);
    try {
      if (next === "start") await startInfrastructure();
      else await stopInfrastructure();

      setStatus(
        (current) =>
          current && {
            ...current,
            infrastructure: {
              ...current.infrastructure,
              status: next === "start" ? "running" : "stopped",
            },
          },
      );
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Could not change the infrastructure state.",
      );
    } finally {
      setAction(null);
    }
  }

  if (setupState !== "completed") return null;

  return (
    <article className="setup-card infrastructure-card">
      <div className="setup-card__header">
        <div>
          <span className="card-label">Infrastructure</span>
          <h2>Service status</h2>
        </div>
        <span className={`setup-status setup-status--${infrastructureStatus}`}>
          {infrastructureStatus}
        </span>
      </div>
      <p>Control the Docker services installed on the Raspberry Pi.</p>
      <div className="infrastructure-actions">
        <button
          className="refresh-button"
          type="button"

          onClick={() => window.location.reload()}
        >
          <p>Refresh page</p>
          <GrUpdate size={20} />
        </button>
        <button
          className={`setup-button setup-button--secondary${infrastructureStatus === "running" ? " setup-button--active" : ""}`}
          type="button"
          onClick={() => infrastructure("start")}
          disabled={action !== null || infrastructureStatus === "running"}
          aria-pressed={infrastructureStatus === "running"}
        >
          Start
        </button>
        <button
          className={`setup-button setup-button--danger${infrastructureStatus === "stopped" ? " setup-button--active" : ""}`}
          type="button"
          onClick={() => infrastructure("stop")}
          disabled={action !== null || infrastructureStatus === "stopped"}
          aria-pressed={infrastructureStatus === "stopped"}
        >
          Stop
        </button>
      </div>
    </article>
  );
}
