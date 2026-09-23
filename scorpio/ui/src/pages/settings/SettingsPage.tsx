import { Brand } from "../../components/Brand/Brand";
import { useSettings } from "./hooks/useSettings";
import "./Settings.css";

export function SettingsPage() {
  const {
    message,
    scorpioToken,
    setScorpioToken,
    showScorpioToken,
    setShowScorpioToken,
    scorpioApiUrl,
    setScorpioApiUrl,
    saveScorpioSetup,
  } = useSettings();
  return (
    <main className="settings-page">
      <header className="settings-header">
        <Brand />
        <a href="#/">Back to Home</a>
      </header>
      {message && <div className="settings-message">{message}</div>}
      <section className="settings-content">
        <span className="card-label">Settings</span>
        {/* Token authentication */}
        <h1>Station settings</h1>
        <p>
          Configure the station settings below. The Scorpio API token is required for the station to
          communicate with the Scorpio server.
        </p>
        <form className="settings-card" onSubmit={(e) => saveScorpioSetup(e)}>
          <h2>Scorpio API token</h2>
          <input
            type={showScorpioToken ? "text" : "password"}
            value={scorpioToken}
            onChange={(event) => setScorpioToken(event.target.value)}
            placeholder="Scorpio API token"
            required
          />
          <label>
            <input
              type="checkbox"
              checked={showScorpioToken}
              onChange={(event) => setShowScorpioToken(event.target.checked)}
            />
            Show token
          </label>
          <input
            type="text"
            value={scorpioApiUrl}
            onChange={(event) => setScorpioApiUrl(event.target.value)}
            placeholder="Scorpio API URL"
            required
          />
          <button type="submit">Save</button>
        </form>
      </section>
    </main>
  );
}
