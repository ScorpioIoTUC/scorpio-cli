/** Successful acknowledgement from an action endpoint. */
export type MessageResponse = { message: string };

/** Public JSON error fields used by the HTTP transport. */
export type ErrorPayload = { error?: string; message?: string };

/** Call on unmount to close an SSE connection owned by the caller. */
export type Unsubscribe = () => void;
