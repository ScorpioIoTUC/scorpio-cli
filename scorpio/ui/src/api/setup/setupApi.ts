import { requestJson } from "../http";
import type { DockerLogEvent, SetupEvent, SetupStatus } from "./setupTypes";

export function getSetupStatus(): Promise<SetupStatus> {
  return requestJson<SetupStatus>("/scorpio/setup/status");
}

export function startSetup(): Promise<{ status: string; message: string }> {
  return requestJson("/scorpio/setup", {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export function subscribeToSetup(
  onEvent: (event: SetupEvent) => void,
  onError: () => void,
): () => void {
  const events = new EventSource("/scorpio/setup/events");

  events.onmessage = (message) => {
    try {
      onEvent(JSON.parse(message.data) as SetupEvent);
    } catch {
      onError();
    }
  };

  events.onerror = onError;

  return () => events.close();
}

export function startInfrastructure(): Promise<{ message: string }> {
  return requestJson("/scorpio/start");
}

export function stopInfrastructure(): Promise<{ message: string }> {
  return requestJson("/scorpio/stop");
}

export function subscribeToDockerLogs(
  onLog: (event: DockerLogEvent) => void,
  onError: () => void,
): () => void {
  const events = new EventSource("/scorpio/logs/live");

  events.onmessage = (message) => {
    try {
      onLog(JSON.parse(message.data) as DockerLogEvent);
    } catch {
      onError();
    }
  };

  events.onerror = onError;

  return () => events.close();
}
