import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useSshLogin } from "../../api/ssh/useSshLogin";
import type { SshCredentials, SshSession } from "../../api/ssh/sshTypes";
import { Brand } from "../../components/Brand/Brand";
import "./LoginPage.css";

type LoginPageProps = { onConnected: (session: SshSession) => void };

export function LoginPage({ onConnected }: LoginPageProps) {
  // Collect credentials and establish the remote SSH session.
  const navigate = useNavigate();
  const [credentials, setCredentials] = useState<SshCredentials>({ hostname: "", username: "", password: "" });
  const [showPassword, setShowPassword] = useState(false);
  const { login, isLoading, error } = useSshLogin(onConnected);

  function updateField(field: keyof SshCredentials, value: string) {
    // Update one credential without replacing the other fields.
    setCredentials((current) => ({ ...current, [field]: value }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    // Validate and submit the connection form.
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
        </aside>

        <div className="login-panel">
          <div className="login-panel__heading">
            <span className="eyebrow">SSH Connection</span>
            <h2 id="login-title">Access your Raspberry Pi</h2>
            <p>Enter your Raspberry Pi host name and the SSh credentials (username and password).</p>
          </div>

          <form className="login-form" onSubmit={handleSubmit}>
            <label className="field">
              <span>IP Address or hostname</span>
              <input
                name="hostname"
                value={credentials.hostname}
                onChange={(event) => updateField("hostname", event.target.value)}
                placeholder="192.x.y.z"
                autoComplete="off"
                spellCheck="false"
                required />
              <small>Example: raspberrypi.local or 192.168.1.100</small>
            </label>

            <label className="field">
              <span>User</span>
              <input
                name="username"
                value={credentials.username}
                onChange={(event) => updateField("username", event.target.value)}
                placeholder="scorpio"
                autoComplete="username"
                required />
            </label>

            <label className="field">
              <span>Password</span>
              <span className="password-input">
                <input
                  name="password"
                  type={showPassword ? "text" : "password"}
                  value={credentials.password}
                  onChange={(event) => updateField("password", event.target.value)}
                  placeholder="Your SSH password"
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
                  Connecting...</>
                : <>Access <span aria-hidden="true">→</span></>}
            </button>
          </form>

          <p className="login-panel__hint">Ensure that both devices are connected to the same local network.</p>
        </div>
      </section>
    </main>
  );
}
