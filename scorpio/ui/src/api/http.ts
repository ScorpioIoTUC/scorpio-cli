const API_BASE_URL = (import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");

type ErrorPayload = { error?: string; message?: string };

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
    throw new ApiError(
      payload.error ?? payload.message ?? "No se pudo completar la solicitud.",
      response.status,
    );
  }

  return payload;
}
