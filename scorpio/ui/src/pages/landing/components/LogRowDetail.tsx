import type { SetupLog, DockerLog } from "../../../api/setup/setupTypes";

export function LogRowDetail({ log }: { log: SetupLog | DockerLog }) {
  // Render a detailed view of a single log entry.
  const docker = "service" in log;
  const timestamp = log.timestamp ?? new Date().toISOString();
  const level = log.level ?? "info";
  return (
    <div className="log-detail-card">
      <div>
        <strong>Source:</strong> {docker ? log.service : log.module}
      </div>
      <div>
        <strong>Date / time:</strong> {new Date(timestamp).toLocaleString("en-US")}
      </div>
      <div>
        <strong>Level:</strong> {level.toUpperCase()}
      </div>
      <div>
        <strong>Layer:</strong> {docker ? (log.layer ?? "service") : (log.step_id ?? "setup")}
      </div>
      <div>
        <strong>Message:</strong> {log.message}
      </div>
    </div>
  );
}
