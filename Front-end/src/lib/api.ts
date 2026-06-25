// ============================================================
// PaySentinelIQ — API Client
// Base fetch wrapper with auth token injection and error handling
// ============================================================

import { useAuthStore } from "@/stores";
import type { APIError } from "@/types";

// Em produção, NEXT_PUBLIC_API_URL é definido pela Vercel.
// Em desenvolvimento, o desenvolvedor deve criar .env.local com:
//   NEXT_PUBLIC_API_URL=https://api.paysentineliq.com
// Se não houver env var, não é seguro assumir localhost — falhamos cedo.
const RAW_API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;
if (!RAW_API_BASE_URL && typeof window !== "undefined") {
  console.error(
    "[PaySentinelIQ] NEXT_PUBLIC_API_URL is not defined. " +
    "Please set it in your .env.local or Vercel environment variables."
  );
}

/**
 * Normalized base URL — always ends with /api.
 * If the user-provided URL already includes /api, it is kept as-is;
 * otherwise /api is appended so that all path references can omit
 * the /api prefix (e.g. "/payrolls/..." instead of "/api/payrolls/...").
 */
const API_BASE_URL = RAW_API_BASE_URL
  ? RAW_API_BASE_URL.replace(/\/+$/, "") + (RAW_API_BASE_URL.includes("/api") ? "" : "/api")
  : undefined;

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
 * Attempt to refresh the access token using the stored refresh token.
 * Returns the new access token, or null if refresh failed.
 */
async function tryRefreshToken(): Promise<string | null> {
  const { refreshToken, logout, setToken, setRefreshToken } = useAuthStore.getState();
  if (!refreshToken) return null;

  try {
    const base = API_BASE_URL;
    if (!base) return null;

    const res = await fetch(`${base}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!res.ok) {
      logout();
      return null;
    }

    const data = await res.json();
    // The backend returns TokenResponse with access_token and refresh_token
    if (data.access_token) {
      setToken(data.access_token);
      if (data.refresh_token) {
        setRefreshToken(data.refresh_token);
      }
      return data.access_token;
    }
    return null;
  } catch {
    return null;
  }
}

/**
 * Core fetch wrapper. Gets auth token from Zustand store.
 * Throws ApiClientError on non-2xx responses.
 * Automatically retries once with a refreshed token on 401.
 */
async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { params, body, headers: extraHeaders, ...rest } = options;

  const execute = async (tokenOverride?: string): Promise<T> => {
    const token = tokenOverride ?? useAuthStore.getState().token;

    const headers: HeadersInit = {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...extraHeaders,
    };

    const timeoutSignal = AbortSignal.timeout(8_000);
    const combinedSignal = rest.signal
      ? AbortSignal.any([rest.signal, timeoutSignal])
      : timeoutSignal;

    return fetch(buildUrl(path, params), {
      ...rest,
      headers,
      body: body ? JSON.stringify(body) : undefined,
      credentials: "include",
      signal: combinedSignal,
    }).then(async (response) => {
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
    });
  };

  try {
    return await execute();
  } catch (error) {
    // If the error is a 401, try refreshing the token
    if (error instanceof ApiClientError && error.status === 401) {
      const newToken = await tryRefreshToken();
      if (newToken) {
        // Retry once with the new token
        return execute(newToken);
      }
      // Refresh failed — the ApiClientError propagates to React Query.
      // The UI (dashboard) falls back to zeros instead of showing a
      // visitor/guest state. The user remains authenticated.
      if (typeof window !== "undefined") {
        console.error(
          "[PSI Auth] Refresh falhou — token inválido ou backend offline. " +
          "Página usará fallback (zeros)."
        );
      }
    }
    throw error;
  }
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
