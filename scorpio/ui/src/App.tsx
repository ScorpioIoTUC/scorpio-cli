import { useState } from "react";
import { HashRouter, Navigate, Route, Routes } from "react-router-dom";

import type { SshSession } from "./api/ssh/sshTypes";
import { clearSshSession, readSshSession, saveSshSession } from "./helpers/sshSessionStorage";
import { LandingPage } from "./pages/landing/LandingPage";
import { LoginPage } from "./pages/login/LoginPage";

export default function App() {
  const [session, setSession] = useState<SshSession | null>(readSshSession);

  function handleConnected(nextSession: SshSession) {
    saveSshSession(nextSession);
    setSession(nextSession);
  }

  function handleDisconnected() {
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
