// ============================================================
// PaySentinelIQ — AI Assistant Slide-Out Panel
// Chat-like interface for AI-powered payroll & fraud Q&A
// Connected to real backend /api/ai-assistant/chat endpoint
// ============================================================

"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useTranslations } from "next-intl";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/stores";
import { Bot, X, Send, Sparkles, ArrowRight, Loader2, AlertCircle } from "lucide-react";
import { useAIChat, useAIChatSuggestions, type AIChatResponse } from "@/hooks/useApi";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  isError?: boolean;
}

const LOCAL_SUGGESTION_KEYS = [
  "suggestFraudSummary",
  "suggestRiskTrends",
  "suggestComplianceCheck",
  "suggestUnusualActivity",
] as const;

/** Fallback message when the backend is unreachable */
const FALLBACK_RESPONSE =
  "Desculpe, não consegui me conectar ao servidor agora. " +
  "Por favor, tente novamente em alguns instantes. " +
  "Se o problema persistir, verifique sua conexão ou contate o suporte.";

export function AIAssistantPanel() {
  const t = useTranslations("assistant");
  const aiPanelOpen = useUIStore((s) => s.aiPanelOpen);
  const toggleAiPanel = useUIStore((s) => s.toggleAiPanel);

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  // ── API mutation ── //
  const chatMutation = useAIChat();

  // ── Fetch suggestions from backend ── //
  const { data: suggestionsData } = useAIChatSuggestions();
  const backendSuggestions = suggestionsData?.suggestions ?? [];

  // ── Auto-scroll to bottom ── //
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, chatMutation.isPending]);

  // ── Focus input when panel opens ── //
  useEffect(() => {
    if (aiPanelOpen) {
      setTimeout(() => inputRef.current?.focus(), 100);
      // Show greeting if no messages yet
      if (messages.length === 0) {
        setMessages([
          {
            id: "greeting",
            role: "assistant",
            content: t("greeting"),
            timestamp: new Date(),
          },
        ]);
      }
    }
  }, [aiPanelOpen]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Keyboard: Escape to close ── //
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape" && aiPanelOpen) {
        toggleAiPanel();
      }
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [aiPanelOpen, toggleAiPanel]);

  // ── Focus trap within panel ── //
  const handlePanelKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Escape") {
        e.stopPropagation();
        toggleAiPanel();
      }
    },
    [toggleAiPanel]
  );

  // ── Send message via API ── //
  const sendMessage = useCallback(
    (text: string) => {
      if (!text.trim() || chatMutation.isPending) return;
      const trimmed = text.trim();

      const userMsg: Message = {
        id: `user-${Date.now()}`,
        role: "user",
        content: trimmed,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMsg]);
      setInput("");

      chatMutation.mutate(
        { message: trimmed, conversation_id: conversationId ?? undefined },
        {
          onSuccess: (data: AIChatResponse) => {
            setConversationId(data.conversation_id);
            const aiMsg: Message = {
              id: `ai-${Date.now()}`,
              role: "assistant",
              content: data.message,
              timestamp: new Date(),
            };
            setMessages((prev) => [...prev, aiMsg]);
          },
          onError: () => {
            const errorMsg: Message = {
              id: `ai-${Date.now()}-error`,
              role: "assistant",
              content: FALLBACK_RESPONSE,
              timestamp: new Date(),
              isError: true,
            };
            setMessages((prev) => [...prev, errorMsg]);
          },
        }
      );
    },
    [chatMutation, conversationId]
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  const handleSuggestionClick = (key: string) => {
    const label = t(key);
    sendMessage(label);
  };

  const isWaiting = chatMutation.isPending;

  return (
    <AnimatePresence>
      {aiPanelOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm lg:hidden"
            onClick={toggleAiPanel}
            aria-hidden="true"
          />

          {/* Panel */}
          <motion.aside
            ref={panelRef}
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 26, stiffness: 300 }}
            onKeyDown={handlePanelKeyDown}
            role="complementary"
            aria-label={t("panelTitle")}
            className={cn(
              "fixed right-0 top-0 z-50 flex h-dvh w-full flex-col border-l border-psi-border bg-psi-graphite shadow-2xl",
              "sm:w-[420px] lg:relative lg:z-0 lg:h-auto lg:w-[380px] lg:border-l"
            )}
          >
            {/* Header */}
            <div className="flex items-center justify-between border-b border-psi-border px-4 py-3 shrink-0">
              <div className="flex items-center gap-2.5">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-psi-electric/15">
                  <Bot className="h-4.5 w-4.5 text-psi-electric" />
                </div>
                <div>
                  <h2 className="text-sm font-semibold text-psi-text-primary">
                    {t("panelTitle")}
                  </h2>
                  <div className="flex items-center gap-1.5">
                    <span className="h-1.5 w-1.5 rounded-full bg-psi-emerald" />
                    <span className="text-[10px] text-psi-text-secondary">
                      {t("statusOnline")}
                    </span>
                  </div>
                </div>
              </div>
              <button
                onClick={toggleAiPanel}
                className="rounded-lg p-2 text-psi-text-secondary hover:bg-psi-border/40 hover:text-psi-text-primary transition-colors"
                aria-label={t("panelClose")}
              >
                <X className="h-4.5 w-4.5" />
              </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={cn(
                    "flex gap-3",
                    msg.role === "user" && "flex-row-reverse"
                  )}
                >
                  {/* Avatar */}
                  <div
                    className={cn(
                      "flex h-7 w-7 shrink-0 items-center justify-center rounded-full",
                      msg.role === "assistant"
                        ? msg.isError
                          ? "bg-red-500/15"
                          : "bg-psi-electric/15"
                        : "bg-psi-border/50"
                    )}
                  >
                    {msg.role === "assistant" ? (
                      msg.isError ? (
                        <AlertCircle className="h-3.5 w-3.5 text-red-400" />
                      ) : (
                        <Sparkles className="h-3.5 w-3.5 text-psi-electric" />
                      )
                    ) : (
                      <span className="text-[10px] font-bold text-psi-text-secondary">
                        {t("userLabel")}
                      </span>
                    )}
                  </div>

                  {/* Bubble */}
                  <div
                    className={cn(
                      "max-w-[80%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed",
                      msg.role === "assistant"
                        ? msg.isError
                          ? "bg-red-950/30 border border-red-500/30 text-red-200"
                          : "bg-psi-navy/80 border border-psi-border/60 text-psi-text-primary"
                        : "bg-psi-electric/15 text-psi-text-primary"
                    )}
                  >
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                    <span className="block mt-1 text-[10px] text-psi-text-secondary/50">
                      {msg.timestamp.toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  </div>
                </div>
              ))}

              {/* Typing indicator */}
              {isWaiting && (
                <div className="flex gap-3">
                  <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-psi-electric/15">
                    <Sparkles className="h-3.5 w-3.5 text-psi-electric" />
                  </div>
                  <div className="rounded-2xl bg-psi-navy/80 border border-psi-border/60 px-4 py-3">
                    <div className="flex items-center gap-1.5">
                      <Loader2 className="h-3.5 w-3.5 animate-spin text-psi-electric" />
                      <span className="text-xs text-psi-text-secondary">
                        {t("typing")}
                      </span>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Suggestions (only visible with few messages) */}
            {messages.length <= 1 && (
              <div className="px-4 pb-2 shrink-0">
                <div className="flex flex-wrap gap-2">
                  {(backendSuggestions.length > 0
                    ? backendSuggestions
                    : LOCAL_SUGGESTION_KEYS.map((k) => ({ key: k, label: t(k) }))
                  ).map((suggestion) => (
                    <button
                      key={suggestion.key}
                      onClick={() => handleSuggestionClick(suggestion.key)}
                      disabled={isWaiting}
                      className="inline-flex items-center gap-1.5 rounded-full border border-psi-border bg-psi-navy/60 px-3 py-1.5 text-xs text-psi-text-secondary hover:text-psi-text-primary hover:border-psi-electric/40 hover:bg-psi-electric/5 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      <ArrowRight className="h-3 w-3 text-psi-electric" />
                      {suggestion.label}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Input */}
            <form
              onSubmit={handleSubmit}
              className="border-t border-psi-border p-3 shrink-0"
            >
              <div className="flex items-center gap-2">
                <input
                  ref={inputRef}
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder={t("inputPlaceholder")}
                  disabled={isWaiting}
                  className="flex-1 rounded-lg border border-psi-border bg-psi-navy/80 px-3.5 py-2.5 text-sm text-psi-text-primary placeholder:text-psi-text-secondary/50 outline-none focus:border-psi-electric focus:ring-1 focus:ring-psi-electric/30 transition-all disabled:opacity-50"
                  aria-label={t("inputPlaceholder")}
                />
                <button
                  type="submit"
                  disabled={!input.trim() || isWaiting}
                  className="flex h-10 w-10 items-center justify-center rounded-lg bg-psi-electric text-white hover:bg-psi-electric/90 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
                  aria-label={t("send")}
                >
                  <Send className="h-4 w-4" />
                </button>
              </div>
            </form>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}
