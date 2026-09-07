import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useSshLogin } from "../../api/ssh/useSshLogin";
import type { SshCredentials, SshSession } from "../../api/ssh/sshTypes";
import { Brand } from "../../components/Brand/Brand";
import "./LoginPage.css";

type LoginPageProps = { onConnected: (session: SshSession) => void };

export function LoginPage({ onConnected }: LoginPageProps) {
  const navigate = useNavigate();
  const [credentials, setCredentials] = useState<SshCredentials>({ hostname: "", username: "", password: "" });
  const [showPassword, setShowPassword] = useState(false);
  const { login, isLoading, error } = useSshLogin(onConnected);

  function updateField(field: keyof SshCredentials, value: string) {
    setCredentials((current) => ({ ...current, [field]: value }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const connected = await login({
      hostname: credentials.hostname.trim(),
      username: credentials.username.trim(),
      password: credentials.password,
    });
    if (connected) navigate("/", { replace: true });
  }

  return (
    <main className="login-page">
      <section className="login-shell" aria-labelledby="login-title">
        <aside className="login-intro">
          <Brand inverted />
          <div className="login-intro__content">
            <span className="eyebrow eyebrow--light">CONTROL LOCAL</span>
            <h1>Tu estación Scorpio, en un solo lugar.</h1>
            <p>Conecta tu Raspberry Pi para instalar, configurar y monitorear la infraestructura de tu estación.</p>
          </div>
          <div className="login-intro__security">
            <span aria-hidden="true">⌁</span>
            <p>La conexión ocurre en tu red local. Tus credenciales no se guardan en el navegador.</p>
          </div>
          <div className="orbit orbit--one" aria-hidden="true" />
          <div className="orbit orbit--two" aria-hidden="true" />
        </aside>

        <div className="login-panel">
          <div className="login-panel__heading">
            <span className="eyebrow">CONEXIÓN SSH</span>
            <h2 id="login-title">Conecta tu Raspberry Pi</h2>
            <p>Ingresa los mismos datos que utilizas al conectarte por terminal.</p>
          </div>

          <form className="login-form" onSubmit={handleSubmit}>
            <label className="field">
              <span>Dirección IP o hostname</span>
              <input
                name="hostname"
                value={credentials.hostname}
                onChange={(event) => updateField("hostname", event.target.value)}
                placeholder="192.x.y.z"
                autoComplete="off"
                spellCheck="false"
                required />
              <small>Ejemplo: raspberrypi.local o 192.168.1.100</small>
            </label>

            <label className="field">
              <span>Usuario</span>
              <input
                name="username"
                value={credentials.username}
                onChange={(event) => updateField("username", event.target.value)}
                placeholder="scorpio"
                autoComplete="username"
                required />
            </label>

            <label className="field">
              <span>Contraseña</span>
              <span className="password-input">
                <input
                  name="password"
                  type={showPassword ? "text" : "password"}
                  value={credentials.password}
                  onChange={(event) => updateField("password", event.target.value)}
                  placeholder="Tu contraseña SSH"
                  autoComplete="current-password" required />
                <button
                  type="button"
                  className="password-input__toggle"
                  onClick={() => setShowPassword((visible) => !visible)}
                  aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}>
                  {showPassword ? "Ocultar" : "Mostrar"}
                </button>
              </span>
            </label>

            {error &&
              <div className="form-alert" role="alert">
                <span aria-hidden="true">!</span>
                <p>{error}</p>
              </div>}

            <button className="primary-button" type="submit" disabled={isLoading}>
              {isLoading
                ? <>
                  <span className="spinner" aria-hidden="true" />
                  Conectando...</>
                : <>Conectar estación <span aria-hidden="true">→</span></>}
            </button>
          </form>

          <p className="login-panel__hint">Asegúrate de que ambos equipos estén conectados a la misma red.</p>
        </div>
      </section>
    </main>
  );
}
