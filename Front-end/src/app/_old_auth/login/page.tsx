// ============================================================
// PaySentinelIQ — Login Page
// Enterprise-grade login with PSI branding
// ============================================================

"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import Image from "next/image";
import { Mail, Lock, Eye, EyeOff, ShieldCheck } from "lucide-react";
import { cn } from "@/lib/utils";

export default function LoginPage() {
  const router = useRouter();
  const [showPassword, setShowPassword] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!email || !password) {
      setError("Please enter both email and password.");
      return;
    }

    setIsLoading(true);

    // Simulate auth — replace with real API call later
    setTimeout(() => {
      setIsLoading(false);
      router.push("/");
    }, 1500);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
    >
      {/* Logo */}
      <div className="mb-8 text-center">
        <Image
          src="/PSI_Logo2.png"
          alt="PaySentinelIQ"
          width={136}
          height={136}
          className="mx-auto mb-4 h-[136px] w-auto object-contain drop-shadow-xl"
          priority
        />
        <p className="mt-1 text-sm text-psi-text-secondary">
          AI-Powered Payroll Verification & Fraud Intelligence
        </p>
      </div>

      {/* Login Card */}
      <Card glow>
        <CardHeader>
          <CardTitle>Sign In</CardTitle>
          <CardDescription>
            Access your enterprise risk intelligence dashboard
          </CardDescription>
        </CardHeader>

        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            {/* Error */}
            {error && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                className="rounded-lg border border-psi-fraud/40 bg-psi-fraud/10 px-4 py-3 text-sm text-psi-fraud"
              >
                {error}
              </motion.div>
            )}

            {/* Email */}
            <div className="space-y-2">
              <label
                htmlFor="email"
                className="block text-xs font-medium text-psi-text-secondary uppercase tracking-wider"
              >
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-psi-text-secondary" />
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="analyst@paysentineliq.com"
                  className={cn(
                    "w-full rounded-lg border bg-psi-navy/50 py-2.5 pl-10 pr-4 text-sm text-psi-text-primary placeholder:text-psi-text-secondary/40 outline-none transition-colors",
                    "border-psi-border focus:border-psi-electric focus:ring-1 focus:ring-psi-electric"
                  )}
                  autoComplete="email"
                  autoFocus
                />
              </div>
            </div>

            {/* Password */}
            <div className="space-y-2">
              <label
                htmlFor="password"
                className="block text-xs font-medium text-psi-text-secondary uppercase tracking-wider"
              >
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-psi-text-secondary" />
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  className={cn(
                    "w-full rounded-lg border bg-psi-navy/50 py-2.5 pl-10 pr-10 text-sm text-psi-text-primary placeholder:text-psi-text-secondary/40 outline-none transition-colors",
                    "border-psi-border focus:border-psi-electric focus:ring-1 focus:ring-psi-electric"
                  )}
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-psi-text-secondary hover:text-psi-text-primary transition-colors"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>

            {/* Options */}
            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 text-xs text-psi-text-secondary cursor-pointer">
                <input
                  type="checkbox"
                  className="rounded border-psi-border bg-psi-navy/50 accent-psi-electric"
                />
                Remember me
              </label>
              <a
                href="#"
                className="text-xs font-medium text-psi-electric hover:text-psi-electric/80 transition-colors"
              >
                Forgot password?
              </a>
            </div>
          </CardContent>

          <CardFooter className="flex-col gap-4">
            <Button
              type="submit"
              variant="primary"
              size="lg"
              className="w-full"
              loading={isLoading}
            >
              Sign In to PaySentinelIQ
            </Button>

            {/* MFA Indicator */}
            <div className="flex items-center justify-center gap-2 text-xs text-psi-text-secondary">
              <ShieldCheck className="h-3.5 w-3.5 text-psi-emerald" />
              <span>MFA-Protected Login · SOC 2 Compliant</span>
            </div>
          </CardFooter>
        </form>
      </Card>

      {/* Footer */}
      <p className="mt-6 text-center text-xs text-psi-text-secondary">
        Need access?{" "}
        <a href="#" className="font-medium text-psi-electric hover:underline">
          Contact your administrator
        </a>
      </p>
    </motion.div>
  );
}
