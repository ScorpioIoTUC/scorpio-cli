import { FiAlertTriangle, FiCheckCircle, FiLoader } from "react-icons/fi";

import type { InfraUpdateStatus } from "../../../api/update/updateTypes";

type NavigationAction = { onHome: () => void };

export function CheckingUpdates() {
  return <section className="update-state" aria-live="polite">
    <FiLoader className="update-state__spinner" size={34} aria-hidden="true" />
    <h1>Checking for updates</h1>
    <p>Comparing Scorpio CLI and Scorpio Project versions.</p>
  </section>;
}

export function UpdatingSystem() {
  return <section className="update-state" aria-live="polite" aria-busy="true">
    <FiLoader className="update-state__spinner" size={38} aria-hidden="true" />
    <h1>Updating system…</h1>
    <p>Keep this window open while Scorpio installs the required updates.</p>
  </section>;
}

export function UpdateInstalled({ seconds }: { seconds: number }) {
  return <section className="update-state update-state--success" aria-live="polite">
    <FiCheckCircle size={42} aria-hidden="true" />
    <h1>Update installed</h1>
    <p>Scorpio is up to date. Redirecting to Home in {seconds} seconds…</p>
  </section>;
}

export function UpdateFailed({ error, onHome }: NavigationAction & { error: string }) {
  return <section className="update-state update-state--error" role="alert">
    <FiAlertTriangle size={42} aria-hidden="true" />
    <h1>The update could not be installed</h1>
    <p>An internal error occurred while updating Scorpio.</p>
    <pre>{error}</pre>
    <button type="button" onClick={onHome}>Back to Home</button>
  </section>;
}

export function UpdateAvailable({ status, onUpdate }: {
  status: InfraUpdateStatus;
  onUpdate: () => void;
}) {
  const needsUpdate = status.scorpio_cli.need_to_update
    || status.scorpio_project.need_to_update;

  return <section className="update-overview">
    <div className={`update-callout ${needsUpdate ? "update-callout--available" : ""}`}>
      <div>
        <span className="eyebrow">SYSTEM UPDATE</span>
        <h1>{needsUpdate ? "A new Scorpio update is available" : "Scorpio is up to date"}</h1>
        <p>{needsUpdate
          ? "Install the latest required components in one step."
          : "Both Scorpio CLI and Scorpio Project use their latest releases."}</p>
      </div>
      {needsUpdate && <button type="button" onClick={onUpdate}>Update Scorpio</button>}
    </div>
    <div className="version-summary">
      <VersionRow name="Scorpio CLI" status={status.scorpio_cli} />
      <VersionRow name="Scorpio Project" status={status.scorpio_project} />
    </div>
  </section>;
}

function VersionRow({ name, status }: {
  name: string;
  status: InfraUpdateStatus["scorpio_cli"];
}) {
  return <article>
    <div><strong>{name}</strong><span>Installed {status.installed_version}</span></div>
    <div className="version-summary__latest">
      <span>Latest {status.latest_version}</span>
      <strong className={status.need_to_update ? "is-update" : "is-current"}>
        {status.need_to_update ? "Update available" : "Current"}
      </strong>
    </div>
  </article>;
}
