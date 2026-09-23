import { useCallback, useEffect, useState } from "react";
import { getVersion } from "../../../api/version/versionApi";
import type { ProjectVersions } from "../../../api/version/versionTypes";
import { getScorpioUpdateStatus, updateScorpio } from "../../../api/update/updateApi";
import type { ScorpioUpdateResult, ScorpioUpdateStatus } from "../../../api/update/updateTypes";

/** Load version data and coordinate an upgrade on the local UI host. */
export function useUpdates() {
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
        requestError instanceof Error ? requestError.message : "Could not load update information.",
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
      setVersions(
        (current) =>
          current && {
            ...current,
            scorpio_cli: updateResult.installed_version,
          },
      );
      setStatus(
        (current) =>
          current && {
            ...current,
            current_version: updateResult.installed_version,
            need_to_update: false,
          },
      );
    } catch (requestError) {
      setError(
        requestError instanceof Error ? requestError.message : "Scorpio CLI could not be updated.",
      );
    } finally {
      setUpdating(false);
    }
  }

  const reportedCliVersion = status?.current_version;
  const currentCliVersion =
    reportedCliVersion && reportedCliVersion !== "unknown"
      ? reportedCliVersion
      : versions?.scorpio_cli;
  const hasComparableVersions = Boolean(
    status &&
    !status.error &&
    status.current_version !== "unknown" &&
    status.latest_version !== "unknown",
  );

  return {
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
  };
}
