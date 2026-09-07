import { useNavigate } from "react-router-dom";

import type { SshSession } from "../../api/ssh/sshTypes";
import { useSshLogout } from "../../api/ssh/useSshLogout";
import { Brand } from "../../components/Brand/Brand";
import "./LandingPage.css";

type LandingPageProps = { session: SshSession; onDisconnected: () => void };

export function LandingPage({ session, onDisconnected }: LandingPageProps) {
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
          <span className="connection-status"><span aria-hidden="true" /> Conectado</span>
          <button className="text-button" type="button" onClick={logout} disabled={isLoading}>
            {isLoading ? "Desconectando…" : "Desconectar"}
          </button>
        </div>
      </header>

      <section className="landing-content" aria-labelledby="landing-title">
        <div className="landing-hero">
          <span className="eyebrow">ESTACIÓN CONECTADA</span>
          <h1 id="landing-title">Hola, <span>{session.username}</span>.</h1>
          <p>La conexión SSH está lista. Desde aquí podrás instalar y administrar Scorpio en tu Raspberry Pi.</p>
        </div>

        {error && <div className="landing-alert" role="alert">{error}</div>}

        <div className="landing-grid">
          <article className="connection-card">
            <div className="connection-card__icon" aria-hidden="true">⌁</div>
            <div>
              <span className="card-label">CONEXIÓN ACTIVA</span>
              <h2>{session.hostname}</h2>
              <p>Sesión iniciada como {session.username}</p>
            </div>
            <span className="connection-card__check" aria-label="Conexión correcta">✓</span>
          </article>

          <article className="next-card">
            <span className="card-label">SIGUIENTE ETAPA</span>
            <h2>Preparar la instalación</h2>
            <p>En esta sección aparecerán la confirmación del setup, su progreso y los eventos enviados por Scorpio.</p>
            <span className="next-card__tag">Próximamente</span>
          </article>
        </div>
      </section>
    </main>
  );
}
