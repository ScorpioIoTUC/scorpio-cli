const API_BASE_URL = (import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");

type ErrorPayload = { error?: string; message?: string; details?: string };

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function requestJson<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  // Centralize JSON requests and normalize API errors.
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...options.headers,
    },
  });
  const payload = (await response.json().catch(() => ({}))) as T & ErrorPayload;

  if (!response.ok) {
    const message = payload.error ?? payload.message ?? "The request could not be completed.";
    throw new ApiError(
      payload.details ? `${message} ${payload.details}` : message,
      response.status,
    );
  }

  return payload;
}
