import { useCallback, useEffect, useState } from "react";
import { FiHome } from "react-icons/fi";
import { useNavigate } from "react-router-dom";

import { getInfraUpdateStatus, updateInfrastructure } from "../../api/update/updateApi";
import type { InfraUpdateStatus } from "../../api/update/updateTypes";
import { Brand } from "../../components/Brand/Brand";
import {
  CheckingUpdates,
  UpdateAvailable,
  UpdateFailed,
  UpdateInstalled,
  UpdatingSystem,
} from "./elements/UpdateStateViews";
import "./UpdatesPage.css";

type UpdateView = "checking" | "ready" | "updating" | "success" | "error";

export function UpdatesPage() {
  const navigate = useNavigate();
  const [view, setView] = useState<UpdateView>("checking");
  const [status, setStatus] = useState<InfraUpdateStatus | null>(null);
  const [error, setError] = useState("");
  const [redirectSeconds, setRedirectSeconds] = useState(3);

  const loadStatus = useCallback(async () => {
    setView("checking");
    setError("");
    try {
      let result = await getInfraUpdateStatus();
      setStatus(result);
      setView("ready");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not check for updates.");
      setView("error");
    }
  }, []);

  useEffect(() => {
    void loadStatus();
  }, [loadStatus]);

  useEffect(() => {
    if (view !== "success") return undefined;
    const interval = window.setInterval(() => {
      setRedirectSeconds((current) => Math.max(current - 1, 0));
    }, 1_000);
    const redirect = window.setTimeout(() => navigate("/", { replace: true }), 3_000);
    return () => {
      window.clearInterval(interval);
      window.clearTimeout(redirect);
    };
  }, [navigate, view]);

  async function installUpdate() {
    setView("updating");
    setError("");
    try {
      await updateInfrastructure();
      setRedirectSeconds(3);
      setView("success");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unknown update error.");
      setView("error");
    }
  }

  return <main className="updates-page">
    <header className="updates-header">
      <Brand />
      <button type="button" onClick={() => navigate("/")} aria-label="Back to Home">
        <FiHome size={20} aria-hidden="true" />
      </button>
    </header>
    <div className="updates-content">
      {view === "checking" && <CheckingUpdates />}
      {view === "ready" && status &&
        <UpdateAvailable status={status} onUpdate={() => void installUpdate()} />}
      {view === "updating" && <UpdatingSystem />}
      {view === "success" && <UpdateInstalled seconds={redirectSeconds} />}
      {view === "error" &&
        <UpdateFailed error={error} onHome={() => navigate("/")} />}
    </div>
  </main>;
}
