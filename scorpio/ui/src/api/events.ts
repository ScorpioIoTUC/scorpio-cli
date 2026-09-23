import type { Unsubscribe } from "./contracts";

/**
 * Subscribe to same-origin SSE, as required by the existing server/proxy setup.
 * JSON requests use VITE_API_URL; event streams intentionally retain their
 * existing relative URL behavior. The caller owns cleanup via the return value.
 * EventSource keeps its native reconnection behavior; malformed JSON and
 * callback failures notify onError, as before.
 */
export function subscribeToEvents<T>(
  path: string,
  onEvent: (event: T) => void,
  onError: () => void,
): Unsubscribe {
  const events = new EventSource(path);
  events.onmessage = (message) => {
    try {
      onEvent(JSON.parse(message.data) as T);
    } catch {
      onError();
    }
  };
  events.onerror = onError;
  return () => events.close();
}
