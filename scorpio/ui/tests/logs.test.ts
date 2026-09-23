import assert from "node:assert/strict";
import test from "node:test";
import { filterDockerLogs } from "../src/pages/landing/logs/logFilters";
import { getServiceColor } from "../src/pages/landing/logs/serviceColors";
import type { DockerLog } from "../src/api/setup/setupTypes";

const log = (service: string, timestamp: string | null): DockerLog => ({
  service,
  timestamp,
  level: null,
  layer: null,
  message: "test",
});

test("log filters preserve window boundaries, service selection and descending order", () => {
  const now = Date.parse("2026-01-01T12:00:00Z");
  const latest = log("ingest", "2026-01-01T12:00:00Z");
  const boundary = log("ingest", "2026-01-01T11:00:00Z");
  const other = log("export", "2026-01-01T11:30:00Z");
  const expired = log("ingest", "2026-01-01T10:59:59Z");
  const source = [boundary, expired, latest, other, log("ingest", null), log("ingest", "invalid")];
  const original = [...source];
  assert.deepEqual(filterDockerLogs(source, "ingest", "1h", now), [latest, boundary]);
  assert.deepEqual(filterDockerLogs(source, "all", "1h", now), [latest, other, boundary]);
  assert.equal(filterDockerLogs(source, "all", "all", now).length, source.length);
  assert.deepEqual(source, original, "filtering must not reorder the source array");
  assert.equal(getServiceColor("ingest"), getServiceColor("ingest"));
});
