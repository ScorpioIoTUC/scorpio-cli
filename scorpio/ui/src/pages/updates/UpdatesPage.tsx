import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { getVersion } from "../../api/setup/setupApi";
import {
  getScorpioUpdateStatus,
  updateScorpio,
} from "../../api/update/updateApi";
import type {
  ScorpioUpdateResult,
  ScorpioUpdateStatus,
} from "../../api/update/updateTypes";
import { Brand } from "../../components/Brand/Brand";
import "./UpdatesPage.css";

type ProjectVersions = {
  scorpio_cli: string;
  scorpio_project: string;
};

const SCORPIO_CLI_URL = "https://github.com/ScorpioIoTUC/scorpio-cli";
const SCORPIO_PROJECT_URL = "https://github.com/ScorpioIoTUC/Scorpio-Project";

function formatReleaseDate(value: string): string {
  if (!value || value === "unknown") return "Unknown";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

export function UpdatesPage() {
  const [versions, setVersions] = useState<ProjectVersions | null>(null);
  const [status, setStatus] = useState<ScorpioUpdateStatus | null>(null);
  const [result, setResult] = useState<ScorpioUpdateResult | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);

  const loadUpdateInformation = useCallback(async () => {
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const [installedVersions, updateStatus] = await Promise.all([
        getVersion(),
        getScorpioUpdateStatus(),
      ]);
      setVersions(installedVersions);
      setStatus(updateStatus);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Could not load update information.",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadUpdateInformation();
  }, [loadUpdateInformation]);

  async function handleUpdate() {
    setUpdating(true);
    setError("");
    setResult(null);

    try {
      const updateResult = await updateScorpio();
      setResult(updateResult);
      setVersions((current) => current && {
        ...current,
        scorpio_cli: updateResult.installed_version,
      });
      setStatus((current) => current && {
        ...current,
        current_version: updateResult.installed_version,
        need_to_update: false,
      });
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Scorpio CLI could not be updated.",
      );
    } finally {
      setUpdating(false);
    }
  }

  const reportedCliVersion = status?.current_version;
  const currentCliVersion = reportedCliVersion && reportedCliVersion !== "unknown"
    ? reportedCliVersion
    : versions?.scorpio_cli;
  const hasComparableVersions = Boolean(
    status
    && !status.error
    && status.current_version !== "unknown"
    && status.latest_version !== "unknown",
  );

  return (
    <main className="updates-page">
      <header className="updates-header">
        <Brand />
        <Link to="/">Back to Home</Link>
      </header>

      <section className="updates-content" aria-labelledby="updates-title">
        <span className="eyebrow">SYSTEM</span>
        <div className="updates-title-row">
          <div>
            <h1 id="updates-title">Updates</h1>
            <p>Review the installed Scorpio versions and keep the CLI up to date.</p>
          </div>
          <button
            className="updates-refresh"
            type="button"
            onClick={() => void loadUpdateInformation()}
            disabled={loading || updating}
          >
            {loading ? "Checking..." : "Check again"}
          </button>
        </div>

        {error && (
          <div className="updates-notice updates-notice--error" role="alert">
            {error}
          </div>
        )}

        {!loading && status?.error && (
          <div className="updates-notice updates-notice--error" role="alert">
            PyPI could not be reached. Try checking again later.
          </div>
        )}

        {!loading && hasComparableVersions && status?.need_to_update && !result && (
          <div className="updates-notice updates-notice--available">
            <div>
              <strong>A new Scorpio CLI version is available.</strong>
              <span>Update from {status.current_version} to {status.latest_version}.</span>
            </div>
            <button type="button" onClick={() => void handleUpdate()} disabled={updating}>
              {updating ? "Updating..." : "Update"}
            </button>
          </div>
        )}

        {!loading && hasComparableVersions && !status?.need_to_update && !result && (
          <div className="updates-notice updates-notice--success" role="status">
            Scorpio CLI is already up to date.
          </div>
        )}

        {result && (
          <div className="updates-notice updates-notice--success" role="status">
            <div>
              <strong>{result.message}</strong>
              <span>Version {result.installed_version} is installed.</span>
              {result.restart_required && (
                <span>Restart <code>scorpio ui</code> to apply the update.</span>
              )}
            </div>
          </div>
        )}

        <div className="updates-grid" aria-busy={loading}>
          <article className="version-card">
            <span className="version-card__label">Scorpio CLI</span>
            <strong>{currentCliVersion ?? "—"}</strong>
            <dl>
              <div><dt>Latest version</dt><dd>{status?.latest_version ?? "—"}</dd></div>
              <div><dt>Published</dt><dd>{formatReleaseDate(status?.upload_time ?? "")}</dd></div>
            </dl>
            <a href={SCORPIO_CLI_URL} target="_blank" rel="noopener noreferrer">View on GitHub</a>
          </article>

          <article className="version-card">
            <span className="version-card__label">Scorpio Project</span>
            <strong>{versions?.scorpio_project ?? "—"}</strong>
            <p>The installation version currently associated with Scorpio.</p>
            <a href={SCORPIO_PROJECT_URL} target="_blank" rel="noopener noreferrer">View on GitHub</a>
          </article>
        </div>
      </section>
    </main>
  );
}
