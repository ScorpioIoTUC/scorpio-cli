/** Public Discord settings deliberately exclude the stored bot token. */
export type DiscordSettings = {
  configured: boolean;
  channels: Record<string, string>;
  error_alert_gap_minutes: number;
};

export type DiscordResponse = { message: string };
