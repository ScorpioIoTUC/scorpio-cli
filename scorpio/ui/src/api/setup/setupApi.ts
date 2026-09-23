import { requestJson } from "../http";
import { endpoints } from "../endpoints";
import { subscribeToEvents } from "../events";
import type { Unsubscribe } from "../contracts";
import type { SetupEvent, SetupStatus, StartSetupResponse } from "./setupTypes";

/** Read live setup state enriched with persisted installation metadata. */
export function getSetupStatus(): Promise<SetupStatus> {
  return requestJson(endpoints.setup.status);
}

/** Start asynchronously; completion and logs arrive through the SSE stream. */
export function startSetup(): Promise<StartSetupResponse> {
  return requestJson(endpoints.setup.start, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

/** Status snapshots and incremental logs share the same subscription. */
export function subscribeToSetup(
  onEvent: (event: SetupEvent) => void,
  onError: () => void,
): Unsubscribe {
  return subscribeToEvents(endpoints.setup.events, onEvent, onError);
}
