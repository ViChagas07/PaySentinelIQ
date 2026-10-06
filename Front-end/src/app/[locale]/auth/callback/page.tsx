"use client";

import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuthStore } from "@/stores";

export default function GoogleCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const loginStore = useAuthStore((s) => s.login);

  useEffect(() => {
    const accessToken = searchParams.get("access_token");
    const refreshToken = searchParams.get("refresh_token");
    const tokenType = searchParams.get("token_type");
    const expiresIn = searchParams.get("expires_in");
    const error = searchParams.get("error");

    if (error) {
      console.error("Google OAuth callback error:", error);
      router.push(`/?error=${encodeURIComponent(error)}`);
      return;
    }

    if (!accessToken || !refreshToken) {
      console.error("Missing tokens in callback");
      router.push("/?error=missing_tokens");
      return;
    }

    // The backend redirect doesn't include user info in query params for security
    // We need to fetch user info using the access token
    // For now, decode the JWT to get user info (since it's our own JWT)
    try {
      const payload = JSON.parse(atob(accessToken.split(".")[1]));
      
      loginStore(
        {
          id: payload.sub,
          email: payload.email || "",
          full_name: payload.name || payload.email?.split("@")[0] || "User",
          role: payload.role || "viewer",
          tenant_id: payload.tenant_id || "default",
          avatar_url: payload.picture || null,
          mfa_enabled: false,
          last_login: new Date().toISOString(),
          created_at: new Date().toISOString(),
        },
        accessToken,
        refreshToken
      );

      // Clean URL and redirect to dashboard
      window.history.replaceState({}, document.title, window.location.pathname);
      router.push("/dashboard");
    } catch (err) {
      console.error("Failed to parse token:", err);
      router.push("/?error=invalid_token");
    }
  }, [searchParams, loginStore, router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-psi-navy">
      <div className="text-center text-psi-text-secondary">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-psi-electric border-t-transparent mx-auto mb-4" />
        <p>Completando login com Google...</p>
      </div>
    </div>
  );
}