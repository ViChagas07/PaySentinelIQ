// ============================================================
// PaySentinelIQ — Auth Page (Sign In / Sign Up)
// Futuristic design with tabs, Google OIDC, and Resend email
// ============================================================

"use client";

import { useState, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useTranslations, useLocale } from "next-intl";
import { motion, AnimatePresence } from "framer-motion";
import { Card, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import Image from "next/image";
import {
  Mail, Lock, Eye, EyeOff, ShieldCheck, User, Sparkles,
  ArrowRight, CheckCircle2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/stores";
import { AppName } from "@/components/shared/AppName";

// ── Animated Background ── //

function AnimatedBackground() {
  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none" aria-hidden="true">
      {/* Grid */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(56,189,248,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(56,189,248,0.3) 1px, transparent 1px)",
          backgroundSize: "60px 60px",
        }}
      />
      {/* Radial glow */}
      <div className="absolute -top-1/2 left-1/2 -translate-x-1/2 w-[800px] h-[800px] rounded-full bg-psi-electric/5 blur-[120px]" />
      <div className="absolute -bottom-1/3 left-1/4 w-[600px] h-[600px] rounded-full bg-psi-emerald/3 blur-[100px]" />
      {/* Floating orbs */}
      <motion.div
        animate={{ y: [0, -20, 0], opacity: [0.3, 0.6, 0.3] }}
        transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
        className="absolute top-1/4 right-[15%] w-2 h-2 rounded-full bg-psi-electric/40"
      />
      <motion.div
        animate={{ y: [0, 20, 0], opacity: [0.2, 0.5, 0.2] }}
        transition={{ duration: 8, repeat: Infinity, ease: "easeInOut", delay: 1 }}
        className="absolute bottom-1/3 left-[20%] w-1.5 h-1.5 rounded-full bg-psi-emerald/30"
      />
      <motion.div
        animate={{ y: [0, -15, 0], opacity: [0.1, 0.4, 0.1] }}
        transition={{ duration: 7, repeat: Infinity, ease: "easeInOut", delay: 2 }}
        className="absolute top-1/3 left-[10%] w-3 h-3 rounded-full bg-psi-electric/20"
      />
    </div>
  );
}

// ── Tabs ── //

type AuthTab = "signin" | "signup";

// ── Main Page ── //

export default function AuthPage() {
  const t = useTranslations("auth");
  const tc = useTranslations("common");
  const locale = useLocale();
  const router = useRouter();

  const [activeTab, setActiveTab] = useState<AuthTab>("signin");

  // ── Sign In fields ──
  const [signInEmail, setSignInEmail] = useState("");
  const [signInPassword, setSignInPassword] = useState("");
  const [showSignInPassword, setShowSignInPassword] = useState(false);
  const [signInLoading, setSignInLoading] = useState(false);
  const [signInError, setSignInError] = useState("");

  // ── Sign Up fields ──
  const [signUpName, setSignUpName] = useState("");
  const [signUpEmail, setSignUpEmail] = useState("");
  const [signUpPassword, setSignUpPassword] = useState("");
  const [signUpConfirmPassword, setSignUpConfirmPassword] = useState("");
  const [showSignUpPassword, setShowSignUpPassword] = useState(false);
  const [showSignUpConfirmPassword, setShowSignUpConfirmPassword] = useState(false);
  const [signUpLoading, setSignUpLoading] = useState(false);
  const [signUpError, setSignUpError] = useState("");
  const [signUpSuccess, setSignUpSuccess] = useState(false);
  const [agreeToTerms, setAgreeToTerms] = useState(false);

  // ── Google OIDC / GIS Popup OAuth ── //

  useEffect(() => {
    // Load Google Identity Services script if not already present
    if (document.querySelector('script[src="https://accounts.google.com/gsi/client"]')) {
      return;
    }

    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.onerror = () => console.error("Failed to load Google Sign-In script");
    document.body.appendChild(script);

    return () => {
      const existing = document.querySelector('script[src="https://accounts.google.com/gsi/client"]');
      if (existing) {
        document.body.removeChild(existing);
      }
    };
  }, []);

  const loginStore = useAuthStore((s) => s.login);

  const triggerGoogleSignIn = useCallback(() => {
    const google = (window as any).google;
    if (!google?.accounts?.oauth2) {
      console.warn("GIS library not loaded yet");
      setSignInError(t("googleSignInUnavailable"));
      return;
    }

    // Use initTokenClient which opens a REAL browser popup window
    // (unlike the deprecated One Tap prompt() that gets suppressed by browsers)
    const client = google.accounts.oauth2.initTokenClient({
      client_id: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID,
      scope: "openid profile email",
      callback: async (response: any) => {
        if (response.access_token) {
          try {
            const res = await fetch("/api/auth/google", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ access_token: response.access_token }),
            });

            const data = await res.json();

            if (!res.ok) {
              setSignInError(data.error || t("googleSignInFailed"));
              return;
            }

            // Update auth store with user + token from the backend
            if (data.user && data.token) {
              loginStore(data.user, data.token);
            }

            // Success — redirect to dashboard
            router.push(`/${locale}`);
          } catch {
            setSignInError(t("googleSignInRetry"));
          }
        } else if (response.error) {
          console.error("Google OAuth error:", response.error);
          if (response.error === "popup_closed" || response.error === "user_cancelled") {
            setSignInError(t("googleSignInDismissed"));
          } else {
            setSignInError(t("googleSignInFailed"));
          }
        }
      },
    });

    // Request access token — this opens a proper popup window
    client.requestAccessToken();
  }, [locale, router, t, loginStore]);

  // ── Sign In handler ── //
  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setSignInError("");

    if (!signInEmail || !signInPassword) {
      setSignInError(t("validationRequired"));
      return;
    }

    setSignInLoading(true);

    // Simulate auth — TODO: connect to real API
    setTimeout(() => {
      setSignInLoading(false);

      // Persist auth state so the dashboard knows the user is logged in
      loginStore(
        {
          id: crypto.randomUUID(),
          email: signInEmail,
          full_name: signInEmail.split("@")[0] || "Usuário",
          avatar_url: null,
          role: "viewer",
          tenant_id: "demo",
          mfa_enabled: false,
          last_login: new Date().toISOString(),
          created_at: new Date().toISOString(),
        },
        "demo-jwt-token"
      );

      router.push(`/${locale}`);
    }, 1500);
  };

  // ── Sign Up handler ── //
  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    setSignUpError("");

    if (!signUpName) {
      setSignUpError(t("nameRequired"));
      return;
    }
    if (!signUpEmail || !signUpPassword) {
      setSignUpError(t("validationRequired"));
      return;
    }
    if (signUpPassword !== signUpConfirmPassword) {
      setSignUpError(t("passwordsDontMatch"));
      return;
    }
    if (signUpPassword.length < 8) {
      setSignUpError(t("passwordMinLength"));
      return;
    }
    if (!agreeToTerms) {
      setSignUpError(t("mustAgreeToTerms"));
      return;
    }

    setSignUpLoading(true);

    try {
      const res = await fetch("/api/auth/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          fullName: signUpName,
          email: signUpEmail,
          password: signUpPassword,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        setSignUpError(data.error || t("signUpFailed"));
        setSignUpLoading(false);
        return;
      }

      setSignUpSuccess(true);
      setSignUpLoading(false);

      // Persist auth state if the API returns user + token
      if (data.user && data.token) {
        loginStore(data.user, data.token);
      } else {
        // Fallback: set a minimal demo user so the dashboard unlocks
        loginStore(
          {
            id: crypto.randomUUID(),
            email: signUpEmail,
            full_name: signUpName,
            avatar_url: null,
            role: "viewer",
            tenant_id: "demo",
            mfa_enabled: false,
            last_login: new Date().toISOString(),
            created_at: new Date().toISOString(),
          },
          "demo-jwt-token"
        );
      }

      // Auto-redirect after showing success
      setTimeout(() => {
        router.push(`/${locale}`);
      }, 3000);
    } catch {
      setSignUpError(t("networkError"));
      setSignUpLoading(false);
    }
  };

  // ── Render ── //

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-psi-navy overflow-hidden p-4">
      <AnimatedBackground />

      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="relative z-10 w-full max-w-[440px]"
      >
        {/* Logo */}
        <div className="mb-8 text-center">
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <Image
              src="/PSI_Logo2.png"
              alt={tc("appName")}
              width={128}
              height={128}
              className="mx-auto mb-0 h-32 w-auto object-contain drop-shadow-[0_0_24px_rgba(56,189,248,0.3)]"
              priority
            />
          </motion.div>

          {/* App name — locale-aware, with colour highlight matching user's chosen primary colour */}
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.25, ease: "easeOut" }}
          >
            <AppName
              as="h1"
              className="text-xl sm:text-2xl text-psi-text-primary mb-2"
            />
          </motion.div>

          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.35 }}
            className="text-xs text-psi-text-secondary/60 tracking-wide"
          >
            {tc("tagline")}
          </motion.p>
        </div>

        {/* Card */}
        <Card glow className="overflow-hidden border-psi-border/60">
          {/* Tab Switcher */}
          <div className="flex border-b border-psi-border/60">
            <button
              onClick={() => { setActiveTab("signin"); setSignInError(""); }}
              className={cn(
                "flex-1 py-3.5 text-sm font-semibold transition-all relative",
                activeTab === "signin"
                  ? "text-psi-text-primary"
                  : "text-psi-text-secondary/50 hover:text-psi-text-secondary"
              )}
            >
              {t("signInLabel")}
              {activeTab === "signin" && (
                <motion.div
                  layoutId="authTab"
                  className="absolute bottom-0 left-1/4 right-1/4 h-0.5 rounded-full bg-psi-electric"
                  transition={{ type: "spring", stiffness: 500, damping: 30 }}
                />
              )}
            </button>
            <button
              onClick={() => { setActiveTab("signup"); setSignUpError(""); }}
              className={cn(
                "flex-1 py-3.5 text-sm font-semibold transition-all relative",
                activeTab === "signup"
                  ? "text-psi-text-primary"
                  : "text-psi-text-secondary/50 hover:text-psi-text-secondary"
              )}
            >
              {t("signUpLabel")}
              {activeTab === "signup" && (
                <motion.div
                  layoutId="authTab"
                  className="absolute bottom-0 left-1/4 right-1/4 h-0.5 rounded-full bg-psi-electric"
                  transition={{ type: "spring", stiffness: 500, damping: 30 }}
                />
              )}
            </button>
          </div>

          <CardContent className="p-6 sm:p-8">
            <AnimatePresence mode="wait">
              {/* ──────────────── SIGN IN ──────────────── */}
              {activeTab === "signin" && (
                <motion.div
                  key="signin"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ duration: 0.2 }}
                >
                  <form onSubmit={handleSignIn} className="space-y-4">
                    {/* Error */}
                    <AnimatePresence>
                      {signInError && (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: "auto" }}
                          exit={{ opacity: 0, height: 0 }}
                          className="rounded-lg border border-psi-fraud/40 bg-psi-fraud/10 px-4 py-3 text-sm text-psi-fraud"
                        >
                          {signInError}
                        </motion.div>
                      )}
                    </AnimatePresence>

                    {/* Email */}
                    <AuthInput
                      id="signin-email"
                      type="email"
                      icon={Mail}
                      label={t("emailField")}
                      placeholder={t("emailPlaceholder")}
                      value={signInEmail}
                      onChange={setSignInEmail}
                      autoComplete="email"
                      autoFocus
                    />

                    {/* Password */}
                    <AuthInput
                      id="signin-password"
                      type={showSignInPassword ? "text" : "password"}
                      icon={Lock}
                      label={t("passwordField")}
                      placeholder={t("passwordPlaceholder")}
                      value={signInPassword}
                      onChange={setSignInPassword}
                      autoComplete="current-password"
                      showToggle
                      passwordVisible={showSignInPassword}
                      onTogglePassword={() => setShowSignInPassword(!showSignInPassword)}
                      toggleAriaLabel={showSignInPassword ? t("hidePassword") : t("showPassword")}
                    />

                    {/* Remember + Forgot */}
                    <div className="flex items-center justify-between">
                      <label className="flex items-center gap-2 text-xs text-psi-text-secondary cursor-pointer select-none">
                        <input
                          type="checkbox"
                          className="rounded border-psi-border bg-psi-navy/50 accent-psi-electric h-3.5 w-3.5"
                        />
                        {t("rememberMe")}
                      </label>
                      <a href="#" className="text-xs font-medium text-psi-electric hover:text-psi-electric/80 transition-colors">
                        {t("forgotPassword")}
                      </a>
                    </div>

                    {/* Submit */}
                    <Button
                      type="submit"
                      variant="primary"
                      size="lg"
                      className="w-full"
                      loading={signInLoading}
                    >
                      {t("signInToAccount")}
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </Button>

                    {/* Switch to sign-up */}
                    <p className="text-center text-xs text-psi-text-secondary">
                      {t("noAccount")}{" "}
                      <button
                        type="button"
                        onClick={() => setActiveTab("signup")}
                        className="font-semibold text-psi-electric hover:underline"
                      >
                        {t("signUpInstead")}
                      </button>
                    </p>
                  </form>
                </motion.div>
              )}

              {/* ──────────────── SIGN UP ──────────────── */}
              {activeTab === "signup" && (
                <motion.div
                  key="signup"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.2 }}
                >
                  {signUpSuccess ? (
                    /* Success State */
                    <motion.div
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="text-center py-6 space-y-4"
                    >
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ type: "spring", delay: 0.2 }}
                        className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-psi-emerald/15"
                      >
                        <CheckCircle2 className="h-8 w-8 text-psi-emerald" />
                      </motion.div>
                      <h3 className="text-lg font-bold text-psi-text-primary">
                        {t("welcomeEmailSent")}
                      </h3>
                      <p className="text-sm text-psi-text-secondary leading-relaxed">
                        {t("checkYourEmail")}
                      </p>
                      <p className="text-xs text-psi-text-secondary/60">
                        {t("redirectingToDashboard")}
                      </p>
                      {/* Progress bar */}
                      <div className="mx-auto w-48 h-1 rounded-full bg-psi-border/30 overflow-hidden">
                        <motion.div
                          initial={{ width: "0%" }}
                          animate={{ width: "100%" }}
                          transition={{ duration: 3, ease: "linear" }}
                          className="h-full rounded-full bg-psi-electric"
                        />
                      </div>
                    </motion.div>
                  ) : (
                    <form onSubmit={handleSignUp} className="space-y-4">
                      {/* Error */}
                      <AnimatePresence>
                        {signUpError && (
                          <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: "auto" }}
                            exit={{ opacity: 0, height: 0 }}
                            className="rounded-lg border border-psi-fraud/40 bg-psi-fraud/10 px-4 py-3 text-sm text-psi-fraud"
                          >
                            {signUpError}
                          </motion.div>
                        )}
                      </AnimatePresence>

                      {/* Full Name */}
                      <AuthInput
                        id="signup-name"
                        type="text"
                        icon={User}
                        label={t("fullName")}
                        placeholder={t("fullNamePlaceholder")}
                        value={signUpName}
                        onChange={setSignUpName}
                        autoComplete="name"
                        autoFocus
                      />

                      {/* Email */}
                      <AuthInput
                        id="signup-email"
                        type="email"
                        icon={Mail}
                        label={t("emailField")}
                        placeholder={t("emailPlaceholder")}
                        value={signUpEmail}
                        onChange={setSignUpEmail}
                        autoComplete="email"
                      />

                      {/* Password */}
                      <AuthInput
                        id="signup-password"
                        type={showSignUpPassword ? "text" : "password"}
                        icon={Lock}
                        label={t("passwordField")}
                        placeholder={t("passwordPlaceholder")}
                        value={signUpPassword}
                        onChange={setSignUpPassword}
                        autoComplete="new-password"
                        showToggle
                        passwordVisible={showSignUpPassword}
                        onTogglePassword={() => setShowSignUpPassword(!showSignUpPassword)}
                        toggleAriaLabel={showSignUpPassword ? t("hidePassword") : t("showPassword")}
                      />

                      {/* Confirm Password */}
                      <AuthInput
                        id="signup-confirm-password"
                        type={showSignUpConfirmPassword ? "text" : "password"}
                        icon={Lock}
                        label={t("confirmPassword")}
                        placeholder={t("confirmPasswordPlaceholder")}
                        value={signUpConfirmPassword}
                        onChange={setSignUpConfirmPassword}
                        autoComplete="new-password"
                        showToggle
                        passwordVisible={showSignUpConfirmPassword}
                        onTogglePassword={() => setShowSignUpConfirmPassword(!showSignUpConfirmPassword)}
                        toggleAriaLabel={showSignUpConfirmPassword ? t("hidePassword") : t("showPassword")}
                      />

                      {/* Terms */}
                      <label className="flex items-start gap-2 text-xs text-psi-text-secondary cursor-pointer select-none">
                        <input
                          type="checkbox"
                          checked={agreeToTerms}
                          onChange={(e) => setAgreeToTerms(e.target.checked)}
                          className="mt-0.5 rounded border-psi-border bg-psi-navy/50 accent-psi-electric h-3.5 w-3.5"
                        />
                        <span>
                          {t("agreeToTerms")}{" "}
                          <a href="#" className="text-psi-electric hover:underline">{t("termsOfService")}</a>{" "}
                          {tc("and")}{" "}
                          <a href="#" className="text-psi-electric hover:underline">{t("privacyPolicy")}</a>
                        </span>
                      </label>

                      {/* Submit */}
                      <Button
                        type="submit"
                        variant="primary"
                        size="lg"
                        className="w-full"
                        loading={signUpLoading}
                      >
                        <Sparkles className="mr-2 h-4 w-4" />
                        {t("signUpButton")}
                      </Button>

                      {/* Switch to sign-in */}
                      <p className="text-center text-xs text-psi-text-secondary">
                        {t("alreadyHaveAccount")}{" "}
                        <button
                          type="button"
                          onClick={() => setActiveTab("signin")}
                          className="font-semibold text-psi-electric hover:underline"
                        >
                          {t("signInInstead")}
                        </button>
                      </p>
                    </form>
                  )}
                </motion.div>
              )}
            </AnimatePresence>

            {/* ── Divider + Google OIDC (always visible) ── */}
            <div className="mt-6">
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-psi-border/50" />
                </div>
                <div className="relative flex justify-center text-xs">
                  <span className="bg-psi-graphite px-3 text-psi-text-secondary/60">
                    {t("orContinueWith")}
                  </span>
                </div>
              </div>

              {/* Google Button */}
              <button
                type="button"
                onClick={triggerGoogleSignIn}
                className="mt-4 flex w-full items-center justify-center gap-3 rounded-lg border border-psi-border/60 bg-white/[0.03] hover:bg-white/[0.06] px-4 py-2.5 text-sm font-medium text-psi-text-primary transition-all hover:border-psi-border"
              >
                <svg className="h-5 w-5" viewBox="0 0 24 24">
                  <path
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
                    fill="#4285F4"
                  />
                  <path
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    fill="#34A853"
                  />
                  <path
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                    fill="#FBBC05"
                  />
                  <path
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                    fill="#EA4335"
                  />
                </svg>
                {t("googleSignIn")}
              </button>
            </div>

            {/* MFA Footer */}
            <div className="mt-5 flex items-center justify-center gap-2 text-[10px] text-psi-text-secondary/50">
              <ShieldCheck className="h-3 w-3 text-psi-emerald/60" />
              <span>{t("mfaProtected")}</span>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <p className="mt-6 text-center text-[10px] text-psi-text-secondary/40">
          {t("needAccess")}{" "}
          <a href="mailto:support@paysentineliq.com" className="font-medium text-psi-electric/60 hover:text-psi-electric hover:underline transition-colors">
            {t("contactAdmin")}
          </a>
        </p>
      </motion.div>
    </div>
  );
}

// ── Reusable Input Component ── //

interface AuthInputProps {
  id: string;
  type: string;
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  placeholder: string;
  value: string;
  onChange: (value: string) => void;
  autoComplete?: string;
  autoFocus?: boolean;
  showToggle?: boolean;
  passwordVisible?: boolean;
  onTogglePassword?: () => void;
  toggleAriaLabel?: string;
}

function AuthInput({
  id, type, icon: Icon, label, placeholder,
  value, onChange, autoComplete, autoFocus,
  showToggle, passwordVisible, onTogglePassword, toggleAriaLabel,
}: AuthInputProps) {
  return (
    <div className="space-y-1.5">
      <label
        htmlFor={id}
        className="block text-[11px] font-semibold text-psi-text-secondary uppercase tracking-wider"
      >
        {label}
      </label>
      <div className="relative">
        <Icon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-psi-text-secondary/50" />
        <input
          id={id}
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className={cn(
            "w-full rounded-lg border bg-psi-navy/60 py-2.5 text-sm text-psi-text-primary placeholder:text-psi-text-secondary/30 outline-none transition-all",
            showToggle ? "pl-10 pr-10" : "pl-10 pr-4",
            "border-psi-border focus:border-psi-electric focus:ring-1 focus:ring-psi-electric/30"
          )}
          autoComplete={autoComplete}
          autoFocus={autoFocus}
        />
        {showToggle && (
          <button
            type="button"
            onClick={onTogglePassword}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-psi-text-secondary/50 hover:text-psi-text-secondary transition-colors"
            aria-label={toggleAriaLabel}
          >
            {passwordVisible ? (
              <EyeOff className="h-4 w-4" />
            ) : (
              <Eye className="h-4 w-4" />
            )}
          </button>
        )}
      </div>
    </div>
  );
}
