import { requestJson } from "../http";
import type { ScorpioUpdateResult, ScorpioUpdateStatus } from "./updateTypes";

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
