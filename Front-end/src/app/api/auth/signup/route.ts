// ============================================================
// PaySentinelIQ — Sign-Up API Route
// Handles account creation + Resend welcome email
// ============================================================

import { NextRequest, NextResponse } from "next/server";
import { Resend } from "resend";

const resend = new Resend(process.env.RESEND_API_KEY);

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { fullName, email, password } = body;

    // ── Validation ──
    if (!fullName || !email || !password) {
      return NextResponse.json(
        { error: "All fields are required." },
        { status: 400 }
      );
    }

    if (password.length < 8) {
      return NextResponse.json(
        { error: "Password must be at least 8 characters." },
        { status: 400 }
      );
    }

    // ── TODO: Replace with actual DB user creation ──
    // For now, simulate account creation
    const userId = `user_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;

    // ── Send welcome email via Resend ──
    let emailSent = false;
    try {
      const { data, error } = await resend.emails.send({
        from: process.env.RESEND_FROM_EMAIL || "onboarding@paysentineliq.com",
        to: [email],
        subject: "Welcome to PaySentinelIQ — Your AI-Powered Fraud Intelligence Platform",
        html: `
          <!DOCTYPE html>
          <html>
            <head>
              <meta charset="utf-8">
              <meta name="viewport" content="width=device-width, initial-scale=1.0">
            </head>
            <body style="margin:0;padding:0;background-color:#0A1628;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
              <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#0A1628;padding:40px 20px;">
                <tr>
                  <td align="center">
                    <table width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;">
                      <!-- Logo -->
                      <tr>
                        <td align="center" style="padding-bottom:32px;">
                          <h1 style="font-size:28px;font-weight:800;color:#F8FAFC;margin:0;letter-spacing:-0.5px;">
                            ⚡ PaySentinel<span style="color:#38BDF8;">IQ</span>
                          </h1>
                          <p style="font-size:13px;color:#94A3B8;margin:4px 0 0;">AI-Powered Payroll Verification &amp; Fraud Intelligence</p>
                        </td>
                      </tr>
                      <!-- Card -->
                      <tr>
                        <td style="background-color:#111F3A;border:1px solid #1E293B;border-radius:16px;padding:40px 32px;">
                          <h2 style="font-size:22px;font-weight:700;color:#F8FAFC;margin:0 0 12px;">
                            Welcome aboard, ${fullName}!
                          </h2>
                          <p style="font-size:15px;color:#94A3B8;line-height:1.6;margin:0 0 24px;">
                            Your account has been created successfully. You now have access to enterprise-grade payroll verification, real-time fraud detection, and AI-powered risk intelligence.
                          </p>
                          <!-- Feature grid -->
                          <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:24px;">
                            <tr>
                              <td style="padding:12px 16px;background-color:#0A1628;border-radius:10px;margin-bottom:8px;">
                                <p style="font-size:14px;color:#38BDF8;font-weight:600;margin:0 0 2px;">🔍 Fraud Detection</p>
                                <p style="font-size:12px;color:#64748B;margin:0;">AI-powered anomaly detection across payroll batches</p>
                              </td>
                            </tr>
                            <tr><td style="height:8px;"></td></tr>
                            <tr>
                              <td style="padding:12px 16px;background-color:#0A1628;border-radius:10px;">
                                <p style="font-size:14px;color:#10B981;font-weight:600;margin:0 0 2px;">✅ Document Verification</p>
                                <p style="font-size:12px;color:#64748B;margin:0;">OCR + AI validation for identity and payroll documents</p>
                              </td>
                            </tr>
                            <tr><td style="height:8px;"></td></tr>
                            <tr>
                              <td style="padding:12px 16px;background-color:#0A1628;border-radius:10px;">
                                <p style="font-size:14px;color:#A78BFA;font-weight:600;margin:0 0 2px;">📊 Risk Intelligence</p>
                                <p style="font-size:12px;color:#64748B;margin:0;">Real-time dashboards and compliance reporting</p>
                              </td>
                            </tr>
                          </table>
                          <!-- CTA -->
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
                      <!-- Footer -->
                      <tr>
                        <td align="center" style="padding-top:24px;">
                          <p style="font-size:12px;color:#475569;margin:0;">
                            © 2026 PaySentinelIQ. All rights reserved.<br>
                            SOC 2 Type II Compliant · ISO 27001 Certified
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
        console.log("Welcome email sent to:", email, "ID:", data?.id);
      }
    } catch (emailError) {
      console.error("Failed to send welcome email:", emailError);
      // Don't fail the signup if email fails
    }

    return NextResponse.json(
      {
        success: true,
        userId,
        emailSent,
        message: emailSent
          ? "Account created and welcome email sent."
          : "Account created, but welcome email could not be sent.",
      },
      { status: 201 }
    );
  } catch (err) {
    console.error("Signup error:", err);
    return NextResponse.json(
      { error: "Internal server error." },
      { status: 500 }
    );
  }
}
