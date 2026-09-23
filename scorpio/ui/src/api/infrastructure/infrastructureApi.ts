import { requestJson } from "../http";
import { endpoints } from "../endpoints";
import type { MessageResponse } from "../contracts";

/** Legacy backend action uses GET; preserve it during this refactor. */
export function startInfrastructure(): Promise<MessageResponse> {
  return requestJson(endpoints.infrastructure.start);
}

/** Stop services without changing the existing GET endpoint contract. */
export function stopInfrastructure(): Promise<MessageResponse> {
  return requestJson(endpoints.infrastructure.stop);
}

/** Request the remote host reboot; callers retain the confirmation UI. */
export function rebootHost(): Promise<MessageResponse> {
  return requestJson(endpoints.infrastructure.reboot, {
    method: "POST",
    body: JSON.stringify({}),
  });
}
