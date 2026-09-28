import { useEffect, useState } from "react";
import { FiBell, FiLogOut, FiSettings } from "react-icons/fi";
import { useNavigate } from "react-router-dom";

import type { SshSession } from "../../api/ssh/sshTypes";
import { useSshLogout } from "../../api/ssh/useSshLogout";
import { getInfraUpdateStatus } from "../../api/update/updateApi";
import { Brand } from "../../components/Brand/Brand";
import LandingPageGeneral from "./elements/general/LandingPage.general";
import "./LandingPage.css";

type LandingPageProps = { session: SshSession; onDisconnected: () => void };

export function LandingPage({ session, onDisconnected }: LandingPageProps) {
  // Render the connected station shell and dashboard content.
  const navigate = useNavigate();
  const [hasUpdate, setHasUpdate] = useState(false);
  const { logout, isLoading, error } = useSshLogout(() => {
    onDisconnected();
    navigate("/login", { replace: true });
  });

  useEffect(() => {
    let active = true;
    getInfraUpdateStatus().then((status) => {
      if (active) {
        setHasUpdate(
          status.scorpio_cli.need_to_update
          || status.scorpio_project.need_to_update,
        );
      }
    }).catch(() => undefined);
    return () => { active = false; };
  }, []);

  return <main className="landing-page">
    <header className="landing-header">
      <Brand />
      <div className="landing-header__actions">
        <button
          className="header-icon-button header-icon-button--notification"
          type="button"
          onClick={() => navigate("/updates")}
          aria-label={hasUpdate ? "Updates available" : "Open updates"}
          title="Updates"
        >
          <FiBell size={20} aria-hidden="true" />
          {hasUpdate && <span className="notification-badge" aria-hidden="true" />}
        </button>
        <button
          className="header-icon-button"
          type="button"
          onClick={() => navigate("/settings")}
          aria-label="Open settings"
          title="Settings"
        >
          <FiSettings size={20} aria-hidden="true" />
        </button>
        <button
          className="header-icon-button"
          type="button"
          onClick={logout}
          disabled={isLoading}
          aria-label={isLoading ? "Disconnecting" : "Disconnect"}
          title="Disconnect"
        >
          <FiLogOut size={20} aria-hidden="true" />
        </button>
      </div>
    </header>
    <section className="landing-content" aria-labelledby="landing-title">
      {error && <div className="landing-alert" role="alert">{error}</div>}
      <LandingPageGeneral />
    </section>
  </main>;
}
