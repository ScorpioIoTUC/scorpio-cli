import { useNavigate } from "react-router-dom";

import type { SshSession } from "../../api/ssh/sshTypes";
import { useSshLogout } from "./hooks/useSshLogout";
import { Brand } from "../../components/Brand/Brand";
import Dashboard from "./components/Dashboard";
import "./LandingPage.css";

type LandingPageProps = { session: SshSession; onDisconnected: () => void };

export function LandingPage({ session, onDisconnected }: LandingPageProps) {
  // Render the connected station shell and dashboard content.
  const navigate = useNavigate();
  const { logout, isLoading, error } = useSshLogout(() => {
    onDisconnected();
    navigate("/login", { replace: true });
  });

  return (
    <main className="landing-page">
      <header className="landing-header">
        <Brand />
        <div className="landing-header__actions">
          <button className="text-button" type="button" onClick={() => navigate("/settings")}>
            Settings
          </button>
          <button className="text-button" type="button" onClick={() => navigate("/updates")}>
            Updates
          </button>
          <button
            style={{ color: "var(--color-primary)" }}
            className="text-button"
            type="button"
            onClick={logout}
            disabled={isLoading}
          >
            {isLoading ? "Disconnecting…" : "Disconnect"}
          </button>
        </div>
      </header>
      <section className="landing-content" aria-labelledby="landing-title">
        {error && (
          <div className="landing-alert" role="alert">
            {error}
          </div>
        )}
        <Dashboard />
      </section>
    </main>
  );
}
