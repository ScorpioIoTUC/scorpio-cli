import { useState } from "react";

import { sshApi } from "./sshApi";
import type { SshCredentials, SshSession } from "./sshTypes";

export function useSshLogin(onConnected: (session: SshSession) => void) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function login(credentials: SshCredentials): Promise<boolean> {
    setIsLoading(true);
    setError(null);
    try {
      await sshApi.login(credentials);
      onConnected({ hostname: credentials.hostname, username: credentials.username });
      return true;
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "No fue posible conectar con la Raspberry Pi.");
      return false;
    } finally {
      setIsLoading(false);
    }
  }

  return { login, isLoading, error };
}
