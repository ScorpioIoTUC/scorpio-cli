import { endpoints } from "../endpoints";
import { requestJson } from "../http";
import type { ScorpioUpdateResult, ScorpioUpdateStatus } from "./updateTypes";

export function getScorpioUpdateStatus(): Promise<ScorpioUpdateStatus> {
  // Compare the installed CLI version with the latest PyPI release.
  return requestJson<ScorpioUpdateStatus>(endpoints.update);
}

export function updateScorpio(): Promise<ScorpioUpdateResult> {
  // Install the latest CLI version on the computer running the UI server.
  return requestJson<ScorpioUpdateResult>(endpoints.update, {
    method: "POST",
    body: JSON.stringify({}),
  });
}
