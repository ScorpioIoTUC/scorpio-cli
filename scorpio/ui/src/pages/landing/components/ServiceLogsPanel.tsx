import { timeRanges, type TimeRange } from "../logs/logFilters";
import type { useLogFilters } from "../hooks/useLogFilters";
import { LogRows } from "./LogRows";

export function ServiceLogsPanel({ filters }: { filters: ReturnType<typeof useLogFilters> }) {
  const {
    service,
    setService,
    timeRange,
    setTimeRange,
    visibleLogs,
    services,
    serviceColorByName,
  } = filters;
  return (
    <section className="logs-panel">
      <div className="logs-panel__header">
        <div>
          <h2>Service logs</h2>
          <span className="card-label">LIVE INFRASTRUCTURE</span>
        </div>
        <span className="logs-count">{visibleLogs.length} events</span>
      </div>
      <div className="logs-filters logs-filters--services">
        <label>
          Service
          <select value={service} onChange={(event) => setService(event.target.value)}>
            <option value="all">All</option>
            {services.map((item) => (
              <option key={item}>{item}</option>
            ))}
          </select>
        </label>
        <label>
          Time range
          <select
            value={timeRange}
            onChange={(event) => setTimeRange(event.target.value as TimeRange)}
          >
            {Object.entries(timeRanges).map(([value, range]) => (
              <option key={value} value={value}>
                {range.label}
              </option>
            ))}
          </select>
        </label>
      </div>
      <LogRows logs={visibleLogs} service sourceColors={serviceColorByName} />
    </section>
  );
}
