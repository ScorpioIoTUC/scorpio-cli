import { requestJson } from "../http";
import type { InfraUpdateResult, InfraUpdateStatus } from "./updateTypes";

const STATUS_CACHE_TTL_MS = 60_000;

let cachedStatus: InfraUpdateStatus | null = null;
let cacheExpiresAt = 0;
let pendingStatusRequest: Promise<InfraUpdateStatus> | null = null;

export function getInfraUpdateStatus(): Promise<InfraUpdateStatus> {
  // Reuse fresh data and coalesce simultaneous status requests.
  if (cachedStatus && Date.now() < cacheExpiresAt) {
    return Promise.resolve(cachedStatus);
  }

  if (!pendingStatusRequest) {
    pendingStatusRequest = requestJson<InfraUpdateStatus>(
      "/scorpio/infrastructure/update",
    )
      .then((status) => {
        cachedStatus = status;
        cacheExpiresAt = Date.now() + STATUS_CACHE_TTL_MS;
        return status;
      })
      .finally(() => {
        pendingStatusRequest = null;
      });
  }

  return pendingStatusRequest;
}

export function invalidateInfraUpdateStatus(): void {
  // Force the next status check to retrieve current server data.
  cachedStatus = null;
  cacheExpiresAt = 0;
}

export async function updateInfrastructure(): Promise<InfraUpdateResult> {
  // Update whichever Scorpio components are outdated.
  try {
    return await requestJson<InfraUpdateResult>(
      "/scorpio/infrastructure/update",
      {
        method: "POST",
        body: JSON.stringify({}),
      },
    );
  } finally {
    invalidateInfraUpdateStatus();
  }
}
