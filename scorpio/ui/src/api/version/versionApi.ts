import { requestJson } from "../http";
import { endpoints } from "../endpoints";
import type { ProjectVersions } from "./versionTypes";

/** Read the existing version endpoint without initiating an update. */
export function getVersion(): Promise<ProjectVersions> {
  return requestJson(endpoints.version);
}
