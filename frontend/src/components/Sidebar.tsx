import TokenPanel from "./TokenPanel";
import type { SessionStats } from "../types";

interface SidebarProps {
  stats: SessionStats;
  onNewChat: () => void;
}

export default function Sidebar({ stats, onNewChat }: SidebarProps) {
  return (
    <aside className="flex w-72 shrink-0 flex-col border-r border-chat-border bg-chat-sidebar">
      <div className="flex items-center justify-between border-b border-chat-border px-4 py-4">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-chat-accent text-sm font-bold">
            R
          </div>
          <span className="font-medium">Router Agent</span>
        </div>
      </div>

      <div className="p-3">
        <button
          onClick={onNewChat}
          className="flex w-full items-center gap-2 rounded-lg border border-chat-border px-3 py-2.5 text-sm text-white transition hover:bg-chat-surface"
        >
          <span className="text-lg leading-none">+</span>
          Novo chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-4 pb-4">
        <TokenPanel
          sessionBreakdown={stats.token_breakdown}
          totalTokens={stats.total_tokens}
          totalCredits={stats.total_credits}
        />
      </div>

      <div className="border-t border-chat-border p-4 text-xs text-chat-muted">
        <p>{stats.messages} mensagens nesta sessão</p>
        <p className="mt-1">Local: {stats.local_tokens.toLocaleString()} · Remoto: {stats.remote_tokens.toLocaleString()}</p>
      </div>
    </aside>
  );
}