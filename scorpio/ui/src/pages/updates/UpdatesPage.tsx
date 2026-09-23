import { Link } from "react-router-dom";
import { Brand } from "../../components/Brand/Brand";
import { useUpdates } from "./hooks/useUpdates";
import "./UpdatesPage.css";

const SCORPIO_CLI_URL = "https://github.com/ScorpioIoTUC/scorpio-cli";
const SCORPIO_PROJECT_URL = "https://github.com/ScorpioIoTUC/Scorpio-Project";

function formatReleaseDate(value: string): string {
  if (!value || value === "unknown") return "Unknown";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

export function UpdatesPage() {
  const {
    versions,
    status,
    result,
    error,
    loading,
    updating,
    loadUpdateInformation,
    handleUpdate,
    currentCliVersion,
    hasComparableVersions,
  } = useUpdates();
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
              <span>
                Update from {status.current_version} to {status.latest_version}.
              </span>
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
                <span>
                  Restart <code>scorpio ui</code> to apply the update.
                </span>
              )}
            </div>
          </div>
        )}

        <div className="updates-grid" aria-busy={loading}>
          <article className="version-card">
            <span className="version-card__label">Scorpio CLI</span>
            <strong>{currentCliVersion ?? "—"}</strong>
            <dl>
              <div>
                <dt>Latest version</dt>
                <dd>{status?.latest_version ?? "—"}</dd>
              </div>
              <div>
                <dt>Published</dt>
                <dd>{formatReleaseDate(status?.upload_time ?? "")}</dd>
              </div>
            </dl>
            <a href={SCORPIO_CLI_URL} target="_blank" rel="noopener noreferrer">
              View on GitHub
            </a>
          </article>

          <article className="version-card">
            <span className="version-card__label">Scorpio Project</span>
            <strong>{versions?.scorpio_project ?? "—"}</strong>
            <p>The installation version currently associated with Scorpio.</p>
            <a href={SCORPIO_PROJECT_URL} target="_blank" rel="noopener noreferrer">
              View on GitHub
            </a>
          </article>
        </div>
      </section>
    </main>
  );
}
