import { requestJson } from "../http";
import type { InfraUpdateResult, InfraUpdateStatus } from "./updateTypes";

export function getInfraUpdateStatus(): Promise<InfraUpdateStatus> {
  // Compare both installed components with their latest published versions.
  return requestJson<InfraUpdateStatus>("/scorpio/infrastructure/update");
}

export function updateInfrastructure(): Promise<InfraUpdateResult> {
  // Update whichever Scorpio components are outdated.
  return requestJson<InfraUpdateResult>("/scorpio/infrastructure/update", {
    method: "POST",
    body: JSON.stringify({}),
  });
}
