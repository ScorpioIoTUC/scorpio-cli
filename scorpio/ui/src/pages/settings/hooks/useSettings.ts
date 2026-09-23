import { type FormEvent, useEffect, useState } from "react";
import {
  getDiscordSettings,
  removeDiscord,
  setDiscordAlertGap,
  setDiscordChannel,
  setupDiscord,
} from "../../../api/discord/discordApi";
import type { DiscordSettings } from "../../../api/discord/discordTypes";
import { getScorpioTokenSetup, updateScorpioTokenSetup } from "../../../api/token/tokenApi";

/** Preserve settings requests, form actions and the five-second message timer. */
export function useSettings() {
  const [settings, setSettings] = useState<DiscordSettings | null>(null);
  const [discordToken, setDiscordToken] = useState("");
  const [scorpioToken, setScorpioToken] = useState("");
  const [showScorpioToken, setShowScorpioToken] = useState(false);
  const [scorpioApiUrl, setScorpioApiUrl] = useState("");
  const [tag, setTag] = useState("general");
  const [channelId, setChannelId] = useState("");
  const [gap, setGap] = useState(5);
  const [message, setMessage] = useState("");

  useEffect(() => {
    getDiscordSettings()
      .then((value) => {
        setSettings(value);
        setGap(value.error_alert_gap_minutes);
        setChannelId(value.channels.general ?? "");
      })
      .catch(() => setMessage("Could not load Discord settings."));
  }, []);

  useEffect(() => {
    getScorpioTokenSetup()
      .then((result) => {
        setScorpioToken(result.token);
        setScorpioApiUrl(result.api_url);
      })
      .catch(() => setMessage("Could not load Scorpio API settings."));
  }, []);

  useEffect(() => {
    if (!message) return;
    const timeout = window.setTimeout(() => setMessage(""), 5000);
    return () => window.clearTimeout(timeout);
  }, [message]);

  async function saveToken(event: FormEvent) {
    event.preventDefault();
    const result = await setupDiscord(discordToken);
    setMessage(result.message);
    setDiscordToken("");
    setSettings((current) => current && { ...current, configured: true });
  }

  async function saveChannel(event: FormEvent) {
    event.preventDefault();
    const result = await setDiscordChannel(tag, channelId);
    setMessage(result.message);
    setSettings(
      (current) => current && { ...current, channels: { ...current.channels, [tag]: channelId } },
    );
  }

  async function saveGap(event: FormEvent) {
    event.preventDefault();
    const result = await setDiscordAlertGap(gap);
    setMessage(result.message);
  }

  async function removeConfiguration() {
    if (!window.confirm("Remove the Discord configuration?")) return;
    const result = await removeDiscord();
    setMessage(result.message);
    setSettings({ configured: false, channels: {}, error_alert_gap_minutes: 5 });
    setDiscordToken("");
    setChannelId("");
  }

  async function saveScorpioSetup(event: FormEvent) {
    event.preventDefault();
    const token = scorpioToken.trim();
    const apiUrl = scorpioApiUrl.trim() || undefined;
    if (!token) {
      setMessage("Scorpio API token cannot be empty.");
      return;
    }
    const result = await updateScorpioTokenSetup(token, apiUrl);
    setMessage(result.message);
  }

  return {
    settings,
    discordToken,
    setDiscordToken,
    scorpioToken,
    setScorpioToken,
    showScorpioToken,
    setShowScorpioToken,
    scorpioApiUrl,
    setScorpioApiUrl,
    tag,
    setTag,
    channelId,
    setChannelId,
    gap,
    setGap,
    message,
    saveToken,
    saveChannel,
    saveGap,
    removeConfiguration,
    saveScorpioSetup,
  };
}
