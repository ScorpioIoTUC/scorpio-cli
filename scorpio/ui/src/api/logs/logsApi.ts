import { endpoints } from "../endpoints";
import { subscribeToEvents } from "../events";
import type { Unsubscribe } from "../contracts";
import type { DockerLogEvent } from "../setup/setupTypes";

/** Stream Docker log events; close the returned subscription on unmount. */
export function subscribeToDockerLogs(
  onLog: (event: DockerLogEvent) => void,
  onError: () => void,
): Unsubscribe {
  return subscribeToEvents(endpoints.infrastructure.logs, onLog, onError);
}
