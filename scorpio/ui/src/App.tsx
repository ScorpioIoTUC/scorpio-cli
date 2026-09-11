import { useState } from "react";
import { HashRouter, Navigate, Route, Routes } from "react-router-dom";

import type { SshSession } from "./api/ssh/sshTypes";
import { clearSshSession, readSshSession, saveSshSession } from "./helpers/sshSessionStorage";
import { LandingPage } from "./pages/landing/LandingPage";
import { LoginPage } from "./pages/login/LoginPage";
import { SettingsPage } from "./pages/settings/SettingsPage";

export default function App() {
  // Restore the SSH session so the user can reopen the dashboard.
  const [session, setSession] = useState<SshSession | null>(readSshSession);

  function handleConnected(nextSession: SshSession) {
    // Keep the connected station available across page reloads.
    saveSshSession(nextSession);
    setSession(nextSession);
  }

  function handleDisconnected() {
    // Remove the session and return the user to the login flow.
    clearSshSession();
    setSession(null);
  }

  return (
    <HashRouter>
      <Routes>
        <Route
          path="/login"
          element={
            session
              ? <Navigate to="/" replace />
              : <LoginPage onConnected={handleConnected} />} />
        <Route
          path="/settings"
          element={session ? <SettingsPage /> : <Navigate to="/login" replace />} />
        <Route
          path="/"
          element={
            session
              ? <LandingPage session={session} onDisconnected={handleDisconnected} />
              : <Navigate to="/login" replace />} />
        <Route path="*" element={<Navigate to={session ? "/" : "/login"} replace />} />
      </Routes>
    </HashRouter>
  );
}
