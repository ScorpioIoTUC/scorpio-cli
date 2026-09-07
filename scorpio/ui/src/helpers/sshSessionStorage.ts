import type { SshSession } from "../api/ssh/sshTypes";

const SESSION_KEY = "scorpio:ssh-session";

export function readSshSession(): SshSession | null {
  const value = sessionStorage.getItem(SESSION_KEY);
  if (!value) return null;
  try {
    const session = JSON.parse(value) as Partial<SshSession>;
    if (!session.hostname || !session.username) return null;
    return { hostname: session.hostname, username: session.username };
  } catch {
    sessionStorage.removeItem(SESSION_KEY);
    return null;
  }
}

export function saveSshSession(session: SshSession): void {
  sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

export function clearSshSession(): void {
  sessionStorage.removeItem(SESSION_KEY);
}
