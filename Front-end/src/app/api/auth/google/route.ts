// ============================================================
// PaySentinelIQ — Google OIDC Token Verification
// Verifies Google ID token and creates/returns user session
// ============================================================

import { NextRequest, NextResponse } from "next/server";
import { Resend } from "resend";

const resend = new Resend(process.env.RESEND_API_KEY);

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { credential } = body;

    if (!credential) {
      return NextResponse.json(
        { error: "Google credential is required." },
        { status: 400 }
      );
    }

    // ── Verify token with Google ──
    const googleResponse = await fetch(
      `https://oauth2.googleapis.com/tokeninfo?id_token=${credential}`
    );

    if (!googleResponse.ok) {
      return NextResponse.json(
        { error: "Invalid Google token." },
        { status: 401 }
      );
    }

    const googleUser = await googleResponse.json();

    // Validate audience (client ID)
    if (googleUser.aud !== process.env.GOOGLE_CLIENT_ID) {
      return NextResponse.json(
        { error: "Token audience mismatch." },
        { status: 401 }
      );
    }

    const { email, name, picture, sub: googleId, email_verified } = googleUser;

    // ── TODO: Create or find user in DB ──
    const userId = `google_${googleId}`;
    const isNewUser = true; // TODO: Check if user exists

    // ── Send welcome email for new users via Resend ──
    let emailSent = false;
    if (isNewUser) {
      try {
        const displayName = name || email?.split("@")[0] || "there";

        const { data, error } = await resend.emails.send({
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

    return NextResponse.json({
      success: true,
      userId,
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
      { status: 500 }
    );
  }
}
