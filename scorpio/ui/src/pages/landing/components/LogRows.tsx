import { useMemo, useState } from "react";
import type { CSSProperties } from "react";
import type { SetupLog, DockerLog } from "../../../api/setup/setupTypes";
import { getServiceColor } from "../logs/serviceColors";
import { LogRowDetail } from "./LogRowDetail";

type LogRowsProps = {
  logs: Array<SetupLog | DockerLog>;
  service?: boolean;
  sourceColors?: Record<string, string>;
};

export function LogRows({ logs, service = false, sourceColors = {} }: LogRowsProps) {
  // Render normalized setup or Docker events as table rows.
  const [expandedLog, setExpandedLog] = useState<number | null>(null);
  const orderedLogs = useMemo(
    () =>
      [...logs].sort((left, right) => {
        const leftTime = left.timestamp ? Date.parse(left.timestamp) : 0;
        const rightTime = right.timestamp ? Date.parse(right.timestamp) : 0;
        return rightTime - leftTime;
      }),
    [logs],
  );

  return (
    <div className="logs-table">
      <div className="logs-terminal" role="log" aria-live="polite">
        <div className="logs-table-header">
          <span>{service ? "Service" : "Source"}</span>
          <span>Date / time</span>
          <span>Level</span>
          <span>Layer</span>
          <span>Message</span>
          <span className="visually-hidden">Actions</span>
        </div>
        {orderedLogs.length === 0 ? (
          <p className="logs-empty">No events to display.</p>
        ) : (
          orderedLogs.map((log, index) => {
            const docker = "service" in log;
            const timestamp = log.timestamp ?? new Date().toISOString();
            const level = log.level ?? "info";
            const isExpanded = expandedLog === index;
            const source = docker ? log.service : log.module;
            const rowStyle = {
              "--service-color": sourceColors[source] ?? getServiceColor(source),
            } as CSSProperties;
            return (
              <div
                className={`log-line log-line--${level.toLowerCase()}`}
                key={`${timestamp}-${source}-${index}`}
                style={rowStyle}
              >
                <span className="log-service">{source}</span>
                <time>{new Date(timestamp).toLocaleString("en-US")}</time>
                <span className={`log-level log-level--${level.toLowerCase()}`}>
                  {level.toUpperCase()}
                </span>
                <span className="log-layer">
                  {docker ? (log.layer ?? "service") : (log.step_id ?? "setup")}
                </span>
                <span className="log-message" title={log.message}>
                  {log.message}
                </span>
                <button
                  className="log-detail-btn"
                  type="button"
                  aria-label={`${isExpanded ? "Hide" : "Show"} details for event ${index + 1}`}
                  aria-expanded={isExpanded}
                  onClick={() => setExpandedLog(isExpanded ? null : index)}
                >
                  {isExpanded ? "-" : "+"}
                </button>
                {isExpanded && (
                  <div className="log-detail-row">
                    <LogRowDetail log={log} />
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
