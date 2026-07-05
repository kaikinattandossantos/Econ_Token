import type { ChatResponse, SessionStats } from "../types";

const API_BASE = "/api";

export async function sendMessage(message: string): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });

  if (!res.ok) {
    throw new Error(`Erro na API: ${res.status}`);
  }

  return res.json();
}

export async function fetchStats(): Promise<SessionStats> {
  const res = await fetch(`${API_BASE}/stats`);
  if (!res.ok) {
    throw new Error(`Erro ao buscar stats: ${res.status}`);
  }
  return res.json();
}

export async function resetStats(): Promise<void> {
  await fetch(`${API_BASE}/stats/reset`, { method: "POST" });
}