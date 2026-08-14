"use client";

import { useState, useRef, useEffect } from "react";
import { api } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Brain, Send, User, Bot, CloudRain, AlertTriangle, Package, TrendingUp } from "lucide-react";

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: "Bonjour ! Je suis l'assistant IA de DENG PHARMA. Posez-moi vos questions.", timestamp: new Date() }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const suggestions = [
    { icon: CloudRain, text: "Analyse saisonnière" },
    { icon: TrendingUp, text: "Prévisions de ventes" },
    { icon: AlertTriangle, text: "Alertes de stock" },
    { icon: Package, text: "Que commander ?" },
  ];

  const handleSend = async () => {
    if (!input.trim()) return;
    const userMsg: Message = { role: "user", content: input, timestamp: new Date() };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setLoading(true);
    try {
      const data = await api.chatWithAI(input);
      setMessages(prev => [...prev, { role: "assistant", content: data.reply || "Désolé.", timestamp: new Date() }]);
    } catch (err) { setMessages(prev => [...prev, { role: "assistant", content: "Service IA indisponible.", timestamp: new Date() }]); }
    finally { setLoading(false); }
  };

  const handleSuggestion = (text: string) => { setInput(text); setTimeout(() => handleSend(), 100); };

  return (
    <div className="space-y-4 h-[calc(100vh-10rem)] flex flex-col">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-3"><Brain className="w-8 h-8 text-[#0ABAB5]" />Assistant IA</h1>
        <p className="text-slate-500 mt-1">Posez vos questions sur la gestion de votre pharmacie</p>
      </div>

      <Card className="flex-1 border-0 shadow-md overflow-hidden flex flex-col">
        <CardContent className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              {msg.role === "assistant" && <div className="w-8 h-8 bg-gradient-to-br from-[#0ABAB5] to-blue-600 rounded-full flex items-center justify-center"><Bot className="w-4 h-4 text-white" /></div>}
              <div className={`max-w-[70%] rounded-2xl px-4 py-3 ${msg.role === "user" ? "bg-gradient-to-r from-[#0ABAB5] to-blue-600 text-white" : "bg-slate-100 text-slate-800"}`}>
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                <p className={`text-xs mt-1 ${msg.role === "user" ? "text-white/70" : "text-slate-400"}`}>{msg.timestamp.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}</p>
              </div>
              {msg.role === "user" && <div className="w-8 h-8 bg-slate-300 rounded-full flex items-center justify-center"><User className="w-4 h-4 text-slate-600" /></div>}
            </div>
          ))}
          {loading && (
            <div className="flex gap-3">
              <div className="w-8 h-8 bg-gradient-to-br from-[#0ABAB5] to-blue-600 rounded-full flex items-center justify-center"><Bot className="w-4 h-4 text-white" /></div>
              <div className="bg-slate-100 rounded-2xl px-4 py-3"><div className="flex gap-1"><div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" /><div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: "0.1s" }} /><div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }} /></div></div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </CardContent>

        {messages.length <= 1 && (
          <div className="px-6 pb-4">
            <p className="text-xs text-slate-400 mb-2">Suggestions :</p>
            <div className="flex gap-2 flex-wrap">
              {suggestions.map((s, i) => (
                <Badge key={i} variant="secondary" className="cursor-pointer hover:bg-slate-200 py-2 px-3" onClick={() => handleSuggestion(s.text)}>
                  <s.icon className="w-3 h-3 mr-1" />{s.text}
                </Badge>
              ))}
            </div>
          </div>
        )}

        <div className="p-4 border-t">
          <div className="flex gap-3">
            <Input value={input} onChange={e => setInput(e.target.value)} placeholder="Posez votre question..." onKeyDown={e => e.key === 'Enter' && handleSend()} className="h-12" />
            <Button onClick={handleSend} disabled={loading || !input.trim()} className="h-12 px-6 bg-gradient-to-r from-[#0ABAB5] to-blue-600 text-white"><Send className="w-4 h-4" /></Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
