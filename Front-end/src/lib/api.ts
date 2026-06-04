// ============================================================
// PaySentinelIQ — API Client
// Base fetch wrapper with auth token injection and error handling
// ============================================================

import { useAuthStore } from "@/stores";
import type { APIError } from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  params?: Record<string, string | number | boolean | undefined>;
}

export class ApiClientError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public details?: Record<string, string[]>
  ) {
    super(message);
    this.name = "ApiClientError";
  }
}

/**
 * Builds a URL with query parameters, filtering out undefined values.
 */
function buildUrl(path: string, params?: Record<string, string | number | boolean | undefined>): string {
  const url = new URL(`${API_BASE_URL}${path}`);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        url.searchParams.set(key, String(value));
      }
    });
  }
  return url.toString();
}

/**
 * Core fetch wrapper. Gets auth token from Zustand store.
 * Throws ApiClientError on non-2xx responses.
 */
async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { params, body, headers: extraHeaders, ...rest } = options;
  const token = useAuthStore.getState().token;

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...extraHeaders,
  };

  const timeoutSignal = AbortSignal.timeout(8_000);
  const combinedSignal = rest.signal
    ? AbortSignal.any([rest.signal, timeoutSignal])
    : timeoutSignal;

  const response = await fetch(buildUrl(path, params), {
    ...rest,
    headers,
    body: body ? JSON.stringify(body) : undefined,
    credentials: "include",
    signal: combinedSignal,
  });

  if (!response.ok) {
    let errorBody: APIError | undefined;
    try {
      errorBody = await response.json();
    } catch {
      // Response is not JSON
    }

    throw new ApiClientError(
      response.status,
      errorBody?.code || "UNKNOWN_ERROR",
      errorBody?.message || `Request failed with status ${response.status}`,
      errorBody?.details
    );
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

// ── Typed API Methods ── //

export const api = {
  get: <T>(path: string, params?: RequestOptions["params"]) =>
    apiRequest<T>(path, { method: "GET", params }),

  post: <T>(path: string, body?: unknown) =>
    apiRequest<T>(path, { method: "POST", body }),

  put: <T>(path: string, body?: unknown) =>
    apiRequest<T>(path, { method: "PUT", body }),

  patch: <T>(path: string, body?: unknown) =>
    apiRequest<T>(path, { method: "PATCH", body }),

  delete: <T>(path: string) =>
    apiRequest<T>(path, { method: "DELETE" }),
};
