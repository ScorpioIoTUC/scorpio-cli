import { requestJson } from "../http";
import { endpoints } from "../endpoints";
import type { MessageResponse } from "../contracts";
import type { ScorpioTokenSettings } from "./tokenTypes";

export function getScorpioTokenSetup(): Promise<ScorpioTokenSettings> {
  return requestJson(endpoints.setup.token);
}

/** Save the token and URL; server validation and error responses stay unchanged. */
export function updateScorpioTokenSetup(
  newToken: string,
  apiUrl: string | undefined,
): Promise<MessageResponse> {
  return requestJson(endpoints.setup.token, {
    method: "POST",
    body: JSON.stringify({ token: newToken, api_url: apiUrl }),
  });
}
