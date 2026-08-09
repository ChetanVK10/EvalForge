/**
 * Central API client for LLMOps Studio.
 *
 * Directs all frontend requests to the real FastAPI backend using standard `fetch`.
 * Base URL is configurable via VITE_API_BASE_URL (defaults to http://localhost:8000/api/v1).
 */

export const API_BASE_URL =
  (import.meta as any).env?.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

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

export function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Generic HTTP client wrapper calling the real FastAPI backend.
 */
export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  const url = `${API_BASE_URL}${cleanPath}`;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  let response: Response;
  try {
    response = await fetch(url, { ...options, headers });
  } catch (err) {
    throw new ApiError(
      err instanceof Error ? err.message : "Failed to connect to backend API server.",
      503,
      url,
    );
  }

  if (!response.ok) {
    let errorDetail = `Request failed with status ${response.status}`;
    try {
      const data = await response.json();
      if (data.detail) {
        errorDetail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
      } else if (data.message) {
        errorDetail = data.message;
      }
    } catch {
      // Use fallback errorDetail if JSON parsing fails
    }
    throw new ApiError(errorDetail, response.status, url);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return (await response.json()) as T;
}

/**
 * Backward-compatible helper used across service modules.
 * Executes a real HTTP request against path if specified.
 */
export async function request<T>(
  path: string,
  fallbackResolver?: () => T | Promise<T>,
  options: { latencyMs?: number; method?: string; body?: any } = {},
): Promise<T> {
  try {
    const fetchOptions: RequestInit = {
      method: options.method || "GET",
    };
    if (options.body) {
      fetchOptions.body = JSON.stringify(options.body);
    }
    return await apiFetch<T>(path, fetchOptions);
  } catch (err) {
    if (err instanceof ApiError) throw err;
    if (fallbackResolver) {
      return await fallbackResolver();
    }
    throw new ApiError(err instanceof Error ? err.message : "Unexpected API error", 500, path);
  }
}

export function notFound(resource: string, id: string): never {
  throw new ApiError(`${resource} "${id}" was not found.`, 404);
}
