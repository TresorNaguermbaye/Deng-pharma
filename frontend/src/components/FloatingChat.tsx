"use client";

import { useState, useRef, useEffect } from "react";
import { X, Send, User } from "lucide-react";
import { Bot as BotIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";

type Message = {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
};

const SUGGESTIONS = [
  "Stock de Paracétamol",
  "Médicaments en rupture ?",
  "Chiffre d'affaires du mois",
  "Prévision Amoxicilline",
];

export default function FloatingChat() {
  const [open, setOpen] = useState(false);
  const [closing, setClosing] = useState(false);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [hasNewMessage, setHasNewMessage] = useState(true);
  const [wiggle, setWiggle] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Bonjour ! 👋 Je suis l'assistant IA DENG PHARMA. Comment puis-je vous aider aujourd'hui ?",
      timestamp: new Date(),
    },
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const sessionIdRef = useRef<string>(`web-${Math.random().toString(36).slice(2, 10)}`);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Animation "wiggle" du robot toutes les 5s pour attirer l'attention
  useEffect(() => {
    if (open) return;
    const interval = setInterval(() => {
      setWiggle(true);
      setTimeout(() => setWiggle(false), 600);
    }, 8000);
    return () => clearInterval(interval);
  }, [open]);

  const handleClose = () => {
    setClosing(true);
    setTimeout(() => {
      setOpen(false);
      setClosing(false);
    }, 250);
  };

  const handleOpen = () => {
    setOpen(true);
    setHasNewMessage(false);
  };

  const handleSend = async (text?: string) => {
    const msg = (text ?? input).trim();
    if (!msg || loading) return;

    setMessages((prev) => [
      ...prev,
      { role: "user", content: msg, timestamp: new Date() },
    ]);
    setInput("");
    setLoading(true);

    try {
      const data = await api.chatWithAI(msg, sessionIdRef.current);
      const reply =
        data.reply ||
        "🤔 Je n'ai pas compris. Tapez 'aide' pour voir les fonctionnalités.";

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: reply, timestamp: new Date() },
      ]);
    } catch (err) {
      console.error("❌ Erreur chat:", err);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "❌ Erreur de connexion. Vérifiez votre réseau.",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* ─────────── Bouton flottant (icône ROBOT) ─────────── */}
      {!open && (
        <div className="fixed bottom-6 right-6 z-50">
          {/* Anneau de pulsation */}
          <span className="absolute inset-0 rounded-full bg-gradient-to-br from-[#0ABAB5] to-blue-600 animate-pulse-ring pointer-events-none" />

          <button
            onClick={handleOpen}
            onMouseEnter={() => setWiggle(true)}
            onAnimationEnd={() => setWiggle(false)}
            className={`relative w-16 h-16 rounded-full bg-gradient-to-br from-[#0ABAB5] via-blue-500 to-indigo-600 text-white shadow-2xl hover:shadow-[0_0_40px_rgba(10,186,181,0.6)] hover:scale-110 transition-all duration-300 flex items-center justify-center group animate-bot-glow ${
              wiggle ? "animate-bot-wiggle" : ""
            }`}
            aria-label="Ouvrir l'assistant IA"
          >
            {/* Robot SVG custom */}
            <svg
              viewBox="0 0 24 24"
              className="w-8 h-8 group-hover:scale-110 transition"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              {/* Antenne */}
              <line x1="12" y1="3" x2="12" y2="6" />
              <circle cx="12" cy="2.5" r="1" fill="currentColor" />
              {/* Tête */}
              <rect x="5" y="6" width="14" height="11" rx="3" />
              {/* Yeux */}
              <circle cx="9.5" cy="11" r="1.3" fill="currentColor" stroke="none" />
              <circle cx="14.5" cy="11" r="1.3" fill="currentColor" stroke="none" />
              {/* Bouche */}
              <line x1="9.5" y1="14.5" x2="14.5" y2="14.5" />
              {/* Corps */}
              <rect x="9" y="17" width="6" height="3" rx="1" />
            </svg>

            {/* Badge "nouveau message" */}
            {hasNewMessage && (
              <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full border-2 border-white text-[10px] font-bold flex items-center justify-center animate-bounce shadow-lg">
                1
              </span>
            )}
          </button>
        </div>
      )}

      {/* ─────────── Panneau de chat ─────────── */}
      {open && (
        <div
          className={`fixed bottom-6 right-6 z-50 w-[380px] h-[600px] max-h-[85vh] bg-white dark:bg-slate-800 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-700 flex flex-col overflow-hidden ${
            closing ? "animate-float-out" : "animate-float-in"
          }`}
        >
          {/* Header avec robot animé */}
          <div className="relative bg-gradient-to-r from-[#0ABAB5] via-blue-500 to-indigo-600 text-white px-4 py-3 flex items-center justify-between flex-shrink-0 overflow-hidden">
            {/* Effet de vagues en arrière-plan */}
            <div className="absolute inset-0 opacity-20">
              <div className="absolute -top-4 -left-4 w-24 h-24 bg-white rounded-full blur-2xl" />
              <div className="absolute -bottom-4 -right-4 w-32 h-32 bg-white rounded-full blur-2xl" />
            </div>

            <div className="relative flex items-center gap-3">
              {/* Robot animé dans le header */}
              <div className="relative w-10 h-10 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center animate-bounce-in">
                <svg
                  viewBox="0 0 24 24"
                  className="w-6 h-6"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <line x1="12" y1="3" x2="12" y2="6" />
                  <circle cx="12" cy="2.5" r="1" fill="currentColor" />
                  <rect x="5" y="6" width="14" height="11" rx="3" />
                  <circle cx="9.5" cy="11" r="1.3" fill="currentColor" stroke="none" />
                  <circle cx="14.5" cy="11" r="1.3" fill="currentColor" stroke="none" />
                  <line x1="9.5" y1="14.5" x2="14.5" y2="14.5" />
                </svg>
                {/* Point "online" animé */}
                <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-400 rounded-full border-2 border-white animate-pulse" />
              </div>

              <div>
                <p className="font-semibold text-sm">Assistant DENG PHARMA</p>
                <p className="text-xs text-white/90 flex items-center gap-1.5">
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-green-400"></span>
                  </span>
                  En ligne
                </p>
              </div>
            </div>

            <button
              onClick={handleClose}
              className="relative p-1.5 hover:bg-white/20 rounded-full transition hover:rotate-90 duration-300"
              aria-label="Fermer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gradient-to-b from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`flex gap-2 animate-bubble-in ${
                  msg.role === "user" ? "justify-end" : "justify-start"
                }`}
                style={{ animationDelay: `${Math.min(i * 0.05, 0.3)}s` }}
              >
                {msg.role === "assistant" && (
                  <div className="w-7 h-7 bg-gradient-to-br from-[#0ABAB5] to-blue-600 rounded-full flex items-center justify-center flex-shrink-0 shadow-md">
                    <svg
                      viewBox="0 0 24 24"
                      className="w-4 h-4 text-white"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <line x1="12" y1="3" x2="12" y2="6" />
                      <circle cx="12" cy="2.5" r="1" fill="currentColor" />
                      <rect x="5" y="6" width="14" height="11" rx="3" />
                      <circle cx="9.5" cy="11" r="1.3" fill="currentColor" stroke="none" />
                      <circle cx="14.5" cy="11" r="1.3" fill="currentColor" stroke="none" />
                      <line x1="9.5" y1="14.5" x2="14.5" y2="14.5" />
                    </svg>
                  </div>
                )}
                <div
                  className={`max-w-[78%] rounded-2xl px-3 py-2 shadow-sm ${
                    msg.role === "user"
                      ? "bg-gradient-to-r from-[#0ABAB5] to-blue-600 text-white"
                      : "bg-white dark:bg-slate-800 text-slate-800 dark:text-white border border-slate-100 dark:border-slate-700"
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap leading-relaxed">
                    {msg.content}
                  </p>
                  <p
                    className={`text-[10px] mt-1 ${
                      msg.role === "user" ? "text-white/70" : "text-slate-400"
                    }`}
                  >
                    {msg.timestamp.toLocaleTimeString("fr-FR", {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </p>
                </div>
                {msg.role === "user" && (
                  <div className="w-7 h-7 bg-slate-300 dark:bg-slate-600 rounded-full flex items-center justify-center flex-shrink-0">
                    <User className="w-3.5 h-3.5 text-slate-600 dark:text-slate-200" />
                  </div>
                )}
              </div>
            ))}

            {/* Typing indicator avec robot qui "réfléchit" */}
            {loading && (
              <div className="flex gap-2 animate-bubble-in">
                <div className="w-7 h-7 bg-gradient-to-br from-[#0ABAB5] to-blue-600 rounded-full flex items-center justify-center animate-pulse">
                  <svg
                    viewBox="0 0 24 24"
                    className="w-4 h-4 text-white"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <line x1="12" y1="3" x2="12" y2="6" />
                    <circle cx="12" cy="2.5" r="1" fill="currentColor" />
                    <rect x="5" y="6" width="14" height="11" rx="3" />
                    <circle cx="9.5" cy="11" r="1.3" fill="currentColor" stroke="none" />
                    <circle cx="14.5" cy="11" r="1.3" fill="currentColor" stroke="none" />
                    <line x1="9.5" y1="14.5" x2="14.5" y2="14.5" />
                  </svg>
                </div>
                <div className="bg-white dark:bg-slate-800 rounded-2xl px-3 py-3 shadow-sm border border-slate-100 dark:border-slate-700">
                  <div className="flex gap-1.5">
                    <div className="w-2 h-2 bg-[#0ABAB5] rounded-full typing-dot" />
                    <div className="w-2 h-2 bg-[#0ABAB5] rounded-full typing-dot" />
                    <div className="w-2 h-2 bg-[#0ABAB5] rounded-full typing-dot" />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Suggestions */}
          {messages.length <= 1 && (
            <div className="px-3 py-2 bg-white dark:bg-slate-800 border-t border-slate-200 dark:border-slate-700 flex-shrink-0">
              <p className="text-[10px] text-slate-400 mb-1.5 flex items-center gap-1">
                <span className="w-1 h-1 bg-[#0ABAB5] rounded-full" />
                Suggestions
              </p>
              <div className="flex gap-1.5 flex-wrap">
                {SUGGESTIONS.map((s, i) => (
                  <button
                    key={i}
                    onClick={() => handleSend(s)}
                    className="text-[11px] bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-full px-2.5 py-1 hover:bg-[#0ABAB5] hover:text-white hover:border-[#0ABAB5] hover:scale-105 transition-all duration-200"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Input */}
          <div className="p-3 border-t border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 flex-shrink-0">
            <div className="flex gap-2">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                placeholder="Posez votre question..."
                className="h-10 text-sm dark:bg-slate-700 dark:text-white dark:border-slate-600 focus-visible:ring-[#0ABAB5]"
                disabled={loading}
              />
              <Button
                onClick={() => handleSend()}
                disabled={loading || !input.trim()}
                className="h-10 px-3 bg-gradient-to-r from-[#0ABAB5] to-blue-600 text-white hover:scale-105 transition-transform disabled:hover:scale-100"
              >
                <Send className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}