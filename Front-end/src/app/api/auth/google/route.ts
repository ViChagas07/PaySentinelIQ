// ============================================================
// PaySentinelIQ — Google OAuth Consent & Auth Proxy
//
// 1. Accepts Google access_token + LGPD consent from the client
// 2. Proxies to the FastAPI backend for user creation & JWT
// 3. Sends a welcome email via Resend for new users
// 4. Returns the backend's user + JWT to the client
// ============================================================

import { NextRequest, NextResponse } from "next/server";
import { Resend } from "resend";

const resend = new Resend(process.env.RESEND_API_KEY);
const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { access_token, consent_given, terms_version, privacy_version } = body;

    // ── Validate required fields ────────────────────────────
    if (!access_token) {
      return NextResponse.json(
        { error: "Google access token is required." },
        { status: 400 },
      );
    }

    // ── Validate LGPD consent ───────────────────────────────
    if (!consent_given) {
      return NextResponse.json(
        {
          error:
            "Consent to Terms of Service and Privacy Policy is required (LGPD Article 7). "
            + "Please accept the terms before signing in.",
        },
        { status: 403 },
      );
    }

    // ── Verify the access_token with Google's userinfo API ──
    const googleResponse = await fetch(
      "https://www.googleapis.com/oauth2/v3/userinfo",
      {
        headers: { Authorization: `Bearer ${access_token}` },
      },
    );

    if (!googleResponse.ok) {
      const errorText = await googleResponse.text();
      console.error("Google userinfo error:", googleResponse.status, errorText);
      return NextResponse.json(
        { error: "Invalid Google access token." },
        { status: 401 },
      );
    }

    const googleUser = await googleResponse.json();
    const { email, name, picture, sub: googleId } = googleUser;

    // ── Call the FastAPI backend to create/authenticate user ──
    // The backend handles user creation, consent recording, and JWT issuance.
    let backendUser: Record<string, unknown> | null = null;
    let backendToken: string | null = null;
    let isNewUser = false;

    try {
      const backendRes = await fetch(`${BACKEND_URL}/auth/google`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          access_token,
          consent_given: true,
          terms_version: terms_version || "1.0.0",
          privacy_version: privacy_version || "1.0.0",
        }),
      });

      if (backendRes.ok) {
        const backendData = await backendRes.json();
        backendUser = {
          id: backendData.user?.id || `google_${googleId}`,
          email: backendData.user?.email || email,
          full_name: backendData.user?.name || name || email?.split("@")[0] || "User",
          avatar_url: picture || null,
          role: backendData.user?.role || "admin",
          tenant_id: backendData.user?.tenant_id || "tenant_default",
          mfa_enabled: false,
          last_login: new Date().toISOString(),
          created_at: new Date().toISOString(),
        };
        backendToken = backendData.access_token || access_token;
      } else {
        // Backend returned an error — log it but fall back to local user creation
        const errData = await backendRes.json().catch(() => ({}));
        console.warn(
          "Backend auth failed (falling back to local user):",
          backendRes.status,
          errData,
        );
      }
    } catch (proxyErr) {
      // Backend unreachable — fall back to local user creation
      console.warn(
        "Backend unreachable for Google auth (falling back to local user):",
        proxyErr,
      );
    }

    // ── Fallback: create user locally if backend was unavailable ──
    if (!backendUser || !backendToken) {
      const userId = `google_${googleId}`;
      isNewUser = true;

      backendUser = {
        id: userId,
        email,
        full_name: name || email?.split("@")[0] || "User",
        avatar_url: picture || null,
        role: "admin" as const,
        tenant_id: "tenant_default",
        mfa_enabled: false,
        last_login: new Date().toISOString(),
        created_at: new Date().toISOString(),
      };
      backendToken = access_token;
    }

    // ── Send welcome email for new users via Resend ──
    let emailSent = false;
    if (isNewUser) {
      try {
        const displayName = name || email?.split("@")[0] || "there";
        const { error } = await resend.emails.send({
          from: process.env.RESEND_FROM_EMAIL || "onboarding@paysentineliq.com",
          to: [email],
          subject: "Welcome to PaySentinelIQ — Signed in with Google",
          html: `
            <!DOCTYPE html>
            <html>
              <head><meta charset="utf-8"></head>
              <body style="margin:0;padding:0;background-color:#0A1628;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
                <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#0A1628;padding:40px 20px;">
                  <tr>
                    <td align="center">
                      <table width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;">
                        <tr>
                          <td align="center" style="padding-bottom:32px;">
                            <h1 style="font-size:28px;font-weight:800;color:#F8FAFC;margin:0;">
                              ⚡ PaySentinel<span style="color:#38BDF8;">IQ</span>
                            </h1>
                          </td>
                        </tr>
                        <tr>
                          <td style="background-color:#111F3A;border:1px solid #1E293B;border-radius:16px;padding:40px 32px;">
                            <h2 style="font-size:22px;font-weight:700;color:#F8FAFC;margin:0 0 12px;">
                              Welcome, ${displayName}!
                            </h2>
                            <p style="font-size:15px;color:#94A3B8;line-height:1.6;margin:0 0 20px;">
                              You've successfully signed in with Google. Your PaySentinelIQ account is ready to use with full access to AI-powered payroll verification and fraud intelligence.
                            </p>
                            <p style="font-size:14px;color:#64748B;margin:0 0 24px;">
                              Connected account: <strong style="color:#F8FAFC;">${email}</strong>
                            </p>
                            <table width="100%" cellpadding="0" cellspacing="0">
                              <tr>
                                <td align="center">
                                  <a href="${process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000"}/dashboard"
                                     style="display:inline-block;background-color:#38BDF8;color:#0A1628;font-weight:700;font-size:15px;text-decoration:none;padding:14px 36px;border-radius:10px;">
                                    Go to Dashboard →
                                  </a>
                                </td>
                              </tr>
                            </table>
                          </td>
                        </tr>
                        <tr>
                          <td align="center" style="padding-top:24px;">
                            <p style="font-size:12px;color:#475569;margin:0;">
                              © 2026 PaySentinelIQ. All rights reserved.
                            </p>
                          </td>
                        </tr>
                      </table>
                    </td>
                  </tr>
                </table>
              </body>
            </html>
          `,
        });

        if (error) {
          console.error("Resend email error:", error);
        } else {
          emailSent = true;
        }
      } catch (emailError) {
        console.error("Failed to send welcome email:", emailError);
      }
    }

    // ── Return response ─────────────────────────────────────
    return NextResponse.json({
      success: true,
      user: backendUser,
      token: backendToken,
      userId: backendUser?.id,
      email,
      name,
      picture,
      emailSent,
      isNewUser,
    });
  } catch (err) {
    console.error("Google auth error:", err);
    return NextResponse.json(
      { error: "Internal server error." },
      { status: 500 },
    );
  }
}
