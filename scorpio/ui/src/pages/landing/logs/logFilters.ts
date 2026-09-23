import type { DockerLog } from "../../../api/setup/setupTypes";
export const timeRanges = {
  all: { label: "All time", milliseconds: null },
  "15m": { label: "Last 15 minutes", milliseconds: 15 * 60 * 1000 },
  "1h": { label: "Last hour", milliseconds: 60 * 60 * 1000 },
  "24h": { label: "Last 24 hours", milliseconds: 24 * 60 * 60 * 1000 },
  "7d": { label: "Last 7 days", milliseconds: 7 * 24 * 60 * 60 * 1000 },
  "30d": { label: "Last month", milliseconds: 30 * 24 * 60 * 60 * 1000 },
} as const;

export type TimeRange = keyof typeof timeRanges;

/** Preserve filtering, including exclusion of missing/invalid dates in a range. */
export function filterDockerLogs(
  logs: DockerLog[],
  service: string,
  timeRange: TimeRange,
  now: number,
): DockerLog[] {
  const range = timeRanges[timeRange].milliseconds;
  const cutoff = range === null ? null : now - range;
  return logs
    .filter((log) => service === "all" || log.service === service)
    .filter((log) => {
      if (cutoff === null) return true;
      if (!log.timestamp) return false;
      const timestamp = Date.parse(log.timestamp);
      return Number.isFinite(timestamp) && timestamp >= cutoff;
    })
    .sort((left, right) => {
      const leftTime = left.timestamp ? Date.parse(left.timestamp) : 0;
      const rightTime = right.timestamp ? Date.parse(right.timestamp) : 0;
      return rightTime - leftTime;
    });
}
