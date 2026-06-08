"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Switch } from "@/components/ui/Switch";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Bell, Calendar, Clock, Repeat, AlertCircle, Loader2, CheckCircle } from "lucide-react";

// ── Types ──

interface ReminderPreferences {
  every_2_days: boolean;
  weekly: boolean;
  monthly: boolean;
  on_due_date: boolean;
}

const DEFAULT_PREFS: ReminderPreferences = {
  every_2_days: false,
  weekly: false,
  monthly: false,
  on_due_date: true,
};

// ── Reminder option config ──

interface ReminderOption {
  key: keyof ReminderPreferences;
  icon: typeof Bell;
  label: string;
  description: string;
  color: string;
}

const REMINDER_OPTIONS: ReminderOption[] = [
  {
    key: "on_due_date",
    icon: AlertCircle,
    label: "No dia do vencimento",
    description: "Notificar exatamente quando o pagamento vencer",
    color: "text-psi-fraud",
  },
  {
    key: "every_2_days",
    icon: Clock,
    label: "A cada 2 dias",
    description: "Lembretes frequentes conforme a data se aproxima",
    color: "text-psi-warning",
  },
  {
    key: "weekly",
    icon: Repeat,
    label: "Semanalmente",
    description: "Um lembrete por semana antes do vencimento",
    color: "text-psi-electric",
  },
  {
    key: "monthly",
    icon: Calendar,
    label: "Mensalmente",
    description: "Um lembrete por mês antes do vencimento",
    color: "text-psi-emerald",
  },
];

// ── Component ──

export function PaymentRemindersCard() {
  const [prefs, setPrefs] = useState<ReminderPreferences>(DEFAULT_PREFS);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  // Fetch current preferences
  useEffect(() => {
    const fetchPrefs = async () => {
      try {
        const res = await fetch("/api/settings/reminders");
        if (res.ok) {
          const data = await res.json();
          setPrefs(data);
        }
      } catch {
        // Use defaults
      } finally {
        setLoading(false);
      }
    };
    fetchPrefs();
  }, []);

  // Save preferences
  const handleSave = async () => {
    setSaving(true);
    setSaved(false);
    try {
      await fetch("/api/settings/reminders", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(prefs),
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch {
      // Error silently handled
    } finally {
      setSaving(false);
    }
  };

  const handleToggle = (key: keyof ReminderPreferences) => {
    setPrefs((prev) => ({ ...prev, [key]: !prev[key] }));
    setSaved(false);
  };

  if (loading) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <Card glow>
          <CardContent className="flex items-center justify-center py-10">
            <Loader2 className="h-6 w-6 animate-spin text-psi-electric" />
          </CardContent>
        </Card>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <Card glow>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Bell className="h-4 w-4 text-psi-electric" />
            <CardTitle>Lembretes de Pagamento</CardTitle>
          </div>
          <CardDescription>
            Configure com que frequência o PaySentinelIQ deve lembrar você sobre pagamentos pendentes.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {REMINDER_OPTIONS.map((option) => {
              const Icon = option.icon;
              const enabled = prefs[option.key];
              return (
                <div
                  key={option.key}
                  className="flex items-center justify-between rounded-xl border border-white/[0.06] bg-white/[0.02] p-4 hover:border-white/[0.1] transition-colors"
                >
                  <div className="flex items-start gap-3 min-w-0">
                    <div
                      className={`shrink-0 w-10 h-10 rounded-xl flex items-center justify-center ${
                        enabled ? "bg-psi-electric/10" : "bg-psi-border/30"
                      } transition-colors`}
                    >
                      <Icon
                        className={`h-5 w-5 ${enabled ? option.color : "text-psi-text-secondary/50"} transition-colors`}
                      />
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-psi-text-primary">
                        {option.label}
                      </p>
                      <p className="text-xs text-psi-text-secondary/70 mt-0.5">
                        {option.description}
                      </p>
                    </div>
                  </div>
                  <Switch
                    checked={enabled}
                    onCheckedChange={() => handleToggle(option.key)}
                    className="shrink-0 ml-3"
                  />
                </div>
              );
            })}
          </div>

          {/* Active count badge */}
          <div className="flex items-center gap-3 mt-5">
            <Badge variant="primary" className="text-[11px]">
              {Object.values(prefs).filter(Boolean).length} ativo(s)
            </Badge>
            <div className="flex-1" />
            <Button
              onClick={handleSave}
              disabled={saving}
              variant="primary"
              size="sm"
            >
              {saving ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : saved ? (
                <CheckCircle className="h-4 w-4" />
              ) : null}
              {saving ? " Salvando..." : saved ? " Salvo" : "Salvar"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
