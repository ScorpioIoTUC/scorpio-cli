import type { SetupLog } from "../../../api/setup/setupTypes";
import { LogRows } from "./LogRows";

export function LogTable({ title, logs }: { title: string; logs: SetupLog[] }) {
  // Render the setup event table.
  return (
    <section className="logs-panel">
      <div className="logs-panel__header">
        <div>
          <span className="card-label">LIVE ACTIVITY</span>
          <h2>{title}</h2>
        </div>
        <span className="logs-count">{logs.length} events</span>
      </div>
      <LogRows logs={logs} />
    </section>
  );
}
