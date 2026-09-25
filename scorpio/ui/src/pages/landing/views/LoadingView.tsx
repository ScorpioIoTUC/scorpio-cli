import "./LoadingView.css";

type LoadingViewProps = {
  error: string | null;
  onRetry: () => void;
};

export default function LoadingView({ error, onRetry }: LoadingViewProps) {
  return (
    <section className="loading-view" aria-live="polite">
      {!error && <span className="loading-view__spinner" aria-hidden="true" />}
      <span className="card-label">Station status</span>
      <h2>{error ? "Could not load Scorpio" : "Loading Scorpio…"}</h2>
      <p>{error ?? "Checking the installation and infrastructure status."}</p>
      {error && (
        <button className="setup-button" type="button" onClick={onRetry}>
          Try again
        </button>
      )}
    </section>
  );
}
