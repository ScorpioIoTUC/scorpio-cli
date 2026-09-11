import type { SshSession } from "../api/ssh/sshTypes";

const SESSION_KEY = "scorpio:ssh-session";

export function readSshSession(): SshSession | null {
  // Safely restore a valid session from browser storage.
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
  // Persist the active station for the current browser session.
  sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

export function clearSshSession(): void {
  // Remove the active station from browser storage.
  sessionStorage.removeItem(SESSION_KEY);
}
