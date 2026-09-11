import { requestJson } from "../http";

export type DiscordSettings = {
  configured: boolean;
  channels: Record<string, string>;
  error_alert_gap_minutes: number;
};

type DiscordResponse = { message: string };

export function getDiscordSettings() {
  return requestJson<DiscordSettings>("/discord/settings");
}
export function setupDiscord(token: string) {
  console.log("setupDiscord", token);
  return requestJson<DiscordResponse & { configured: boolean }>("/discord/setup",
    { method: "POST", body: JSON.stringify({ token }) }
  );
}
export function setDiscordChannel(tag: string, channel_id: string) {
  return requestJson<DiscordResponse & { channels: Record<string, string> }>("/discord/set-channel",
    { method: "POST", body: JSON.stringify({ tag, channel_id }) }
  );
}
export function setDiscordAlertGap(minutes: number) {
  return requestJson<DiscordResponse & { minutes: number }>("/discord/set-alert-gap",
    { method: "POST", body: JSON.stringify({ minutes }) }
  );
}

export function removeDiscord() {
  return requestJson<DiscordResponse & { configured: boolean }>("/discord/remove", {
    method: "POST",
    body: JSON.stringify({}),
  });
}
