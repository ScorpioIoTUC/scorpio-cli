import { useState } from "react";

import { sshApi } from "./sshApi";

export function useSshLogout(onDisconnected: () => void) {
  // Manage disconnect requests and expose their UI state.
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function logout(): Promise<void> {
    setIsLoading(true);
    setError(null);
    try {
      await sshApi.logout();
      onDisconnected();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "No fue posible cerrar la conexión.");
    } finally {
      setIsLoading(false);
    }
  }

  return { logout, isLoading, error };
}
