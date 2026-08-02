/**
 * Central API client.
 *
 * Today every request is served by the deterministic mock layer in `src/mocks`.
 * When the FastAPI backend lands, only this file changes: swap `mockRequest`
 * for a real `fetch(`${API_BASE_URL}${path}`)` call. Service modules and UI
 * components stay untouched.
 */

export const API_BASE_URL = "/api/v1";

export class ApiError extends Error {
  constructor(
    message: string,
    public status = 500,
    public path?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

const DEFAULT_LATENCY_MS = 220;

export function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Simulates `GET/POST ${API_BASE_URL}${path}` with a small network delay.
 * `resolver` throwing an ApiError propagates like a non-2xx response would.
 */
export async function request<T>(
  path: string,
  resolver: () => T | Promise<T>,
  options: { latencyMs?: number } = {},
): Promise<T> {
  await delay(options.latencyMs ?? DEFAULT_LATENCY_MS);
  try {
    return await resolver();
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError(
      error instanceof Error ? error.message : "Unexpected error",
      500,
      `${API_BASE_URL}${path}`,
    );
  }
}

export function notFound(resource: string, id: string): never {
  throw new ApiError(`${resource} "${id}" was not found.`, 404);
}
