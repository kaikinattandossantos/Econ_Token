import { useCallback, useState } from "react";
import { sendMessage, fetchStats, resetStats } from "./api/client";
import Chat from "./components/Chat";
import Sidebar from "./components/Sidebar";
import type { Message, SessionStats } from "./types";

const emptyStats: SessionStats = {
  total_tokens: 0,
  total_credits: 0,
  local_tokens: 0,
  remote_tokens: 0,
  messages: 0,
  token_breakdown: [],
};

function uid() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [stats, setStats] = useState<SessionStats>(emptyStats);

  const refreshStats = useCallback(async () => {
    try {
      const data = await fetchStats();
      setStats(data);
    } catch {
      /* API offline during dev */
    }
  }, []);

  const handleSubmit = async () => {
    const text = input.trim();
    if (!text || isLoading) return;

    const userMsg: Message = { id: uid(), role: "user", content: text };
    const loadingId = uid();
    const loadingMsg: Message = { id: loadingId, role: "assistant", content: "", isLoading: true };

    setMessages((prev) => [...prev, userMsg, loadingMsg]);
    setInput("");
    setIsLoading(true);

    try {
      const res = await sendMessage(text);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === loadingId
            ? {
                id: loadingId,
                role: "assistant",
                content: res.answer,
                usage: res.usage,
                route: res.route,
              }
            : m
        )
      );
      await refreshStats();
    } catch (err) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === loadingId
            ? {
                id: loadingId,
                role: "assistant",
                content: `Erro: ${err instanceof Error ? err.message : "Falha na requisição"}. Verifique se o backend está rodando em localhost:8000.`,
              }
            : m
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewChat = async () => {
    setMessages([]);
    setInput("");
    setStats(emptyStats);
    try {
      await resetStats();
    } catch {
      /* ignore */
    }
  };

  return (
    <div className="flex h-full">
      <Sidebar stats={stats} onNewChat={handleNewChat} />
      <Chat
        messages={messages}
        input={input}
        onInputChange={setInput}
        onSubmit={handleSubmit}
        isLoading={isLoading}
      />
    </div>
  );
}