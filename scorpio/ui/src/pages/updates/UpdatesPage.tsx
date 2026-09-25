import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { getVersion } from "../../api/setup/setupApi";
import {
  getProjectUpdateStatus,
  getScorpioUpdateStatus,
  updateProjectServices,
  updateScorpio,
} from "../../api/update/updateApi";
import type {
  ProjectUpdateResult,
  ProjectUpdateStatus,
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
  const [projectStatus, setProjectStatus] = useState<ProjectUpdateStatus | null>(null);
  const [projectResult, setProjectResult] = useState<ProjectUpdateResult | null>(null);
  const [projectError, setProjectError] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [updatingProject, setUpdatingProject] = useState(false);

  const loadUpdateInformation = useCallback(async () => {
    setLoading(true);
    setError("");
    setResult(null);
    setProjectResult(null);
    setProjectError("");

    try {
      const [installedVersions, updateStatus, remoteProjectStatus] = await Promise.all([
        getVersion(),
        getScorpioUpdateStatus(),
        getProjectUpdateStatus(),
      ]);
      setVersions(installedVersions);
      setStatus(updateStatus);
      setProjectStatus(remoteProjectStatus);
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
    setProjectError("");
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

  async function handleProjectUpdate() {
    const action = projectStatus?.need_to_update ? "update" : "rebuild";
    if (!window.confirm(
      `This will ${action} Scorpio Project and recreate all Docker services. Continue?`,
    )) return;

    setUpdatingProject(true);
    setError("");
    setProjectError("");
    setProjectResult(null);

    try {
      const updateResult = await updateProjectServices();
      setProjectResult(updateResult);
      setProjectStatus((current) => current && {
        ...current,
        current_version: updateResult.installed_version,
        need_to_update: false,
      });
      setVersions((current) => current && {
        ...current,
        scorpio_project: updateResult.installed_version,
      });
    } catch (requestError) {
      setProjectError(
        requestError instanceof Error
          ? requestError.message
          : "Scorpio services could not be updated.",
      );
    } finally {
      setUpdatingProject(false);
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
            disabled={loading || updating || updatingProject}
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

        {projectResult && (
          <div className="updates-notice updates-notice--success" role="status">
            <div>
              <strong>{projectResult.message}</strong>
              <span>
                Scorpio Project {projectResult.installed_version} is running with rebuilt images.
              </span>
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
            <strong>{projectStatus?.current_version ?? versions?.scorpio_project ?? "—"}</strong>
            <dl>
              <div>
                <dt>Latest release</dt>
                <dd>{projectStatus?.latest_version ?? "—"}</dd>
              </div>
              <div>
                <dt>Remote connection</dt>
                <dd>{projectStatus?.ssh_active ? "Connected" : "Disconnected"}</dd>
              </div>
            </dl>
            <p>
              {projectStatus?.need_to_update
                ? "A newer release is available for the Raspberry Pi."
                : "Rebuild the Docker images to apply the current project code."}
            </p>
            {projectError && (
              <div className="project-update-error" role="alert">
                <strong>Infrastructure update failed.</strong>
                <span>{projectError}</span>
              </div>
            )}
            <button
              className="project-update-button"
              type="button"
              onClick={() => void handleProjectUpdate()}
              disabled={updatingProject || updating || !projectStatus?.ssh_active}
            >
              {updatingProject
                ? "Updating services..."
                : projectStatus?.need_to_update
                  ? "Update infrastructure"
                  : "Rebuild services"}
            </button>
            <a href={SCORPIO_PROJECT_URL} target="_blank" rel="noopener noreferrer">View on GitHub</a>
          </article>
        </div>
      </section>
    </main>
  );
}
