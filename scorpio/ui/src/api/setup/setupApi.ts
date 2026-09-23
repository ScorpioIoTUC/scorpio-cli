import { requestJson } from "../http";
import type { DockerLogEvent, SetupEvent, SetupStatus } from "./setupTypes";

export function getSetupStatus(): Promise<SetupStatus> {
  // Read the persisted setup state from the server.
  return requestJson<SetupStatus>("/scorpio/setup/status");
}

export function startSetup(): Promise<{ status: string; message: string }> {
  // Start the remote setup process.
  return requestJson("/scorpio/setup", {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export function getVersion(): Promise<{scorpio_cli: string, scorpio_project: string}> {
  return requestJson("/version");
}

export function subscribeToSetup(
  onEvent: (event: SetupEvent) => void,
  onError: () => void,
): () => void {
  // Subscribe to setup status and log events through SSE.
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
  // Start all infrastructure services on the remote host.
  return requestJson("/scorpio/start");
}

export function stopInfrastructure(): Promise<{ message: string }> {
  // Stop all infrastructure services on the remote host.
  return requestJson("/scorpio/stop");
}

export function rebootHost(): Promise<{ message: string }> {
  // Request a reboot of the remote host.
  return requestJson("/scorpio/reboot", {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export function subscribeToDockerLogs(
  onLog: (event: DockerLogEvent) => void,
  onError: () => void,
): () => void {
  // Subscribe to live Docker service logs through SSE.
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


// Function to retrieve the configuration token from the server
export function getScorpioTokenSetup(): Promise<{ api_url: string, token: string }> {
  return requestJson("/scorpio/setup/token");
}

// Function to update the configuration token on the server
export function updateScorpioTokenSetup(newToken: string, apiUrl: string | undefined): Promise<{ message: string }> {
  return requestJson("/scorpio/setup/token", {
    method: "POST",
    body: JSON.stringify({ token: newToken, api_url: apiUrl }),
  });
}