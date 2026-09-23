import { requestJson } from "../http";

import type { DiscordSettings, DiscordResponse } from "./discordTypes";
import { endpoints } from "../endpoints";

export function getDiscordSettings() {
  return requestJson<DiscordSettings>(endpoints.discord.settings);
}
export function setupDiscord(token: string) {
  console.log("setupDiscord", token);
  return requestJson<DiscordResponse & { configured: boolean }>(endpoints.discord.setup, {
    method: "POST",
    body: JSON.stringify({ token }),
  });
}
export function setDiscordChannel(tag: string, channel_id: string) {
  return requestJson<DiscordResponse & { channels: Record<string, string> }>(
    endpoints.discord.channel,
    { method: "POST", body: JSON.stringify({ tag, channel_id }) },
  );
}
export function setDiscordAlertGap(minutes: number) {
  return requestJson<DiscordResponse & { minutes: number }>(endpoints.discord.alertGap, {
    method: "POST",
    body: JSON.stringify({ minutes }),
  });
}

export function removeDiscord() {
  return requestJson<DiscordResponse & { configured: boolean }>(endpoints.discord.remove, {
    method: "POST",
    body: JSON.stringify({}),
  });
}
