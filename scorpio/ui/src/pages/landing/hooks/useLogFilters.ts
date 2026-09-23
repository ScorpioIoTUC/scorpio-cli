import { useEffect, useMemo, useState } from "react";
import type { DockerLog } from "../../../api/setup/setupTypes";
import { filterDockerLogs, type TimeRange } from "../logs/logFilters";

/** Refresh the sliding window every 30 seconds and retain service colors. */
export function useLogFilters(dockerLogs: DockerLog[]) {
  const [service, setService] = useState("all");
  const [timeRange, setTimeRange] = useState<TimeRange>("1h");
  const [filterNow, setFilterNow] = useState(Date.now());
  useEffect(() => {
    if (timeRange === "all") return undefined;
    const interval = window.setInterval(() => setFilterNow(Date.now()), 30_000);
    return () => window.clearInterval(interval);
  }, [timeRange]);
  const visibleLogs = useMemo(
    () => filterDockerLogs(dockerLogs, service, timeRange, filterNow),
    [dockerLogs, service, timeRange, filterNow],
  );
  const services = Array.from(new Set(dockerLogs.map((log) => log.service))).sort();
  const serviceColorByName = useMemo(
    () =>
      Object.fromEntries(
        services.map((name, index) => [
          name,
          `hsl(${Math.round((index * 137.508 + 32) % 360)} 68% 46%)`,
        ]),
      ),
    [services],
  );
  return {
    service,
    setService,
    timeRange,
    setTimeRange,
    visibleLogs,
    services,
    serviceColorByName,
  };
}
