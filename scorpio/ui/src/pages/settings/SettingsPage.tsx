import { FormEvent, useEffect, useState } from "react";
import {
  getDiscordSettings, removeDiscord, setDiscordAlertGap, setDiscordChannel, setupDiscord,
  type DiscordSettings,
} from "../../api/discord/discordApi";
import { Brand } from "../../components/Brand/Brand";
import "./Settings.css";

export function SettingsPage() {
  const [settings, setSettings] = useState<DiscordSettings | null>(null);
  const [token, setToken] = useState("");
  const [tag, setTag] = useState("general");
  const [channelId, setChannelId] = useState("");
  const [gap, setGap] = useState(5);
  const [message, setMessage] = useState("");

  useEffect(() => {
    getDiscordSettings().then((value) => {
      setSettings(value);
      setGap(value.error_alert_gap_minutes);
      setChannelId(value.channels.general ?? "");
    }).catch(() => setMessage("Could not load Discord settings."));
  }, []);

  async function saveToken(event: FormEvent) {
    event.preventDefault();
    const result = await setupDiscord(token);
    setMessage(result.message);
    setToken("");
    setSettings((current) => current && { ...current, configured: true });
  }

  async function saveChannel(event: FormEvent) {
    event.preventDefault();
    const result = await setDiscordChannel(tag, channelId);
    setMessage(result.message);
    setSettings((current) => current && { ...current, channels: { ...current.channels, [tag]: channelId } });
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
    setToken("");
    setChannelId("");
  }

  return (
    <main className="settings-page">
      <header className="settings-header"><Brand /><a href="#/">Dashboard</a></header>
      <section className="settings-content">
        <span className="card-label">Settings</span>
        <h1>Discord integration</h1>
        {message && <div className="settings-message">{message}</div>}
        {settings?.configured &&
          <article className="settings-card__configs">
            <h4>Current configuration</h4>
            <p>Bot token: <code>{settings.configured ? "Configured" : "Not configured"}</code></p>
            <p>Channels (Name / ID):</p>
            <ul>
              {Object.entries(settings.channels).map(([tag, channelId]) => (
                <li key={tag}><code>{tag}</code>: <code>#{channelId}</code></li>
              ))}
            </ul>
            <p>Error alert interval: <code>{settings.error_alert_gap_minutes} minutes</code></p>
          </article>
        }


        <form className="settings-card" onSubmit={saveToken}>
          <h2>Bot token</h2><p>{settings?.configured
            ? "You have a token configured. You can update it here."
            : "No token configured"}</p>
          <input
            type="password" value={token} onChange={(event) => setToken(event.target.value)} placeholder="Discord bot token" required />
          <button type="submit">{settings?.configured ? "Update token" : "Save token"}</button>
        </form>
        <form className="settings-card" onSubmit={saveChannel}>
          <h2>Channel</h2>
          <input value={tag} onChange={(event) => setTag(event.target.value)} placeholder="Tag, e.g. alerts" required />
          <input value={channelId} onChange={(event) => setChannelId(event.target.value)} placeholder="Channel ID" required />
          <button type="submit">Save channel</button>
        </form>
        <form className="settings-card" onSubmit={saveGap}>
          <h2>Error alert interval</h2>
          <input type="number" min="1" value={gap} onChange={(event) => setGap(Number(event.target.value))} />
          <span>minutes</span><button type="submit">Save interval</button>
        </form>
        {settings?.configured &&
          <button className="discord-remove-button" type="button" onClick={removeConfiguration}>
            Remove Discord configuration
          </button>}
      </section>
    </main>
  );
}
