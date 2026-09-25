import { requestJson } from "../http";
import type {
  ProjectUpdateResult,
  ProjectUpdateStatus,
  ScorpioUpdateResult,
  ScorpioUpdateStatus,
} from "./updateTypes";

export function getScorpioUpdateStatus(): Promise<ScorpioUpdateStatus> {
  // Compare the installed CLI version with the latest PyPI release.
  return requestJson<ScorpioUpdateStatus>("/scorpio/update");
}

export function updateScorpio(): Promise<ScorpioUpdateResult> {
  // Install the latest CLI version on the computer running the UI server.
  return requestJson<ScorpioUpdateResult>("/scorpio/update", {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export function getProjectUpdateStatus(): Promise<ProjectUpdateStatus> {
  // Compare the project installed on the Raspberry Pi with the latest release.
  return requestJson<ProjectUpdateStatus>("/scorpio/infrastructure/update");
}

export function updateProjectServices(): Promise<ProjectUpdateResult> {
  // Update the remote project and rebuild all Docker service images.
  return requestJson<ProjectUpdateResult>("/scorpio/infrastructure/update", {
    method: "POST",
    body: JSON.stringify({}),
  });
}
