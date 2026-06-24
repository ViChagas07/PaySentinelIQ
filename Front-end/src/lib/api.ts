// ============================================================
// PaySentinelIQ — API Client
// Base fetch wrapper with auth token injection and error handling
// ============================================================

import { useAuthStore } from "@/stores";
import type { APIError } from "@/types";

// Em produção, NEXT_PUBLIC_API_URL é definido pela Vercel.
// Em desenvolvimento, o desenvolvedor deve criar .env.local com:
//   NEXT_PUBLIC_API_URL=https://api.paysentineliq.com/api
// Se não houver env var, não é seguro assumir localhost — falhamos cedo.
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;
if (!API_BASE_URL && typeof window !== "undefined") {
  console.error(
    "[PaySentinelIQ] NEXT_PUBLIC_API_URL is not defined. " +
    "Please set it in your .env.local or Vercel environment variables."
  );
}

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
  const base = API_BASE_URL;
  if (!base) {
    throw new Error(
      "[PaySentinelIQ] NEXT_PUBLIC_API_URL is not configured. " +
      "Cannot make API requests."
    );
  }
  const url = new URL(`${base}${path}`);
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
