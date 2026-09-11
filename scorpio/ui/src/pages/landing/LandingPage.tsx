import { useNavigate } from "react-router-dom";

import type { SshSession } from "../../api/ssh/sshTypes";
import { useSshLogout } from "../../api/ssh/useSshLogout";
import { Brand } from "../../components/Brand/Brand";
import LandingPageGeneral from "./elements/general/LandingPage.general";
import "./LandingPage.css";

type LandingPageProps = { session: SshSession; onDisconnected: () => void };

export function LandingPage({ session, onDisconnected }: LandingPageProps) {
  // Render the connected station shell and dashboard content.
  const navigate = useNavigate();
  const { logout, isLoading, error } = useSshLogout(() => {
    onDisconnected();
    navigate("/login", { replace: true });
  });

  return <main className="landing-page">
    <header className="landing-header">
      <Brand />
      <div className="landing-header__actions">
        <button className="text-button" type="button" onClick={() => navigate("/settings")}>
          Settings
        </button>
        <span className="connection-status"><span aria-hidden="true" /> Conectado</span>
        <button className="text-button" type="button" onClick={logout} disabled={isLoading}>
          {isLoading ? "Desconectando…" : "Desconectar"}
        </button>
      </div>
    </header>
    <section className="landing-content" aria-labelledby="landing-title">
      {error && <div className="landing-alert" role="alert">{error}</div>}
      <LandingPageGeneral />
    </section>
  </main>;
}
