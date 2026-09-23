import type { SetupStatus } from "../../../api/setup/setupTypes";

const labels = {
  idle: "Ready to install",
  running: "Installation in progress",
  completed: "Installation complete",
  failed: "Installation failed",
} as const;

type SetupCardProps = {
  status: SetupStatus | null;
  setupState: SetupStatus["status"];
  progress: number | null;
  setup: () => Promise<void>;
};

export function SetupCard({ status, setupState, progress, setup }: SetupCardProps) {
  return (
    <article className="setup-card">
      <div className="setup-card__header">
        <div>
          <span className="card-label">General</span>
          <h2>{labels[setupState]}</h2>
        </div>
        <span className={`setup-status setup-status--${setupState}`}>{setupState}</span>
      </div>
      {progress !== null && <progress className="setup-progress" max="100" value={progress} />}
      {status?.completedAt && (
        <p className="setup-completed-at">
          Completed on {new Date(status.completedAt).toLocaleString("en-US")}
        </p>
      )}
      {setupState !== "completed" && (
        <>
          <p>
            <span className="setup-warning">⚠️</span>
            Before starting the installation, make sure your Raspberry Pi is connected to the
            internet and has enough free space. The installation process may take several minutes.
          </p>
          <button
            className="setup-button"
            type="button"
            onClick={setup}
            disabled={setupState === "running"}
          >
            Start installation
          </button>
        </>
      )}
    </article>
  );
}
