import type { TokenBreakdownItem, UsageData } from "../types";

interface TokenPanelProps {
  usage?: UsageData;
  sessionBreakdown?: TokenBreakdownItem[];
  totalTokens?: number;
  totalCredits?: number;
  compact?: boolean;
}

const COLORS: Record<string, string> = {
  "Modelo Local": "bg-emerald-500",
  "Modelo Remoto": "bg-amber-500",
};

function BreakdownBar({ items, mode }: { items: TokenBreakdownItem[]; mode: "tokens" | "credits" }) {
  return (
    <div className="space-y-2">
      <div className="flex h-2.5 overflow-hidden rounded-full bg-chat-border">
        {items.map((item) => {
          const pct = mode === "tokens" ? item.percentage : item.credit_percentage;
          if (pct <= 0) return null;
          return (
            <div
              key={`${item.label}-${mode}`}
              className={`${COLORS[item.label] ?? "bg-gray-500"} transition-all`}
              style={{ width: `${pct}%` }}
              title={`${item.label}: ${pct}%`}
            />
          );
        })}
      </div>
      <div className="space-y-1.5">
        {items.map((item) => {
          const pct = mode === "tokens" ? item.percentage : item.credit_percentage;
          const value = mode === "tokens" ? item.tokens : item.credits;
          return (
            <div key={`${item.label}-row-${mode}`} className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <span className={`h-2 w-2 rounded-full ${COLORS[item.label] ?? "bg-gray-500"}`} />
                <span className="text-chat-muted">{item.label}</span>
              </div>
              <div className="text-right">
                <span className="text-white">
                  {mode === "tokens" ? value.toLocaleString() : value.toFixed(6)}
                </span>
                <span className="ml-1.5 text-chat-muted">{pct}%</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function TokenPanel({
  usage,
  sessionBreakdown,
  totalTokens = 0,
  totalCredits = 0,
  compact = false,
}: TokenPanelProps) {
  const breakdown = usage?.credits.breakdown ?? sessionBreakdown ?? [];

  if (compact && usage) {
    return (
      <div className="mt-3 rounded-lg border border-chat-border bg-chat-sidebar/60 p-3 text-xs">
        <div className="mb-2 flex flex-wrap gap-2">
          <span className="rounded-full bg-chat-surface px-2 py-0.5 text-chat-muted">
            {usage.tokens.total.toLocaleString()} tokens
          </span>
          <span className="rounded-full bg-chat-surface px-2 py-0.5 text-chat-muted">
            {usage.credits.total_spent.toFixed(6)} créditos
          </span>
          <span className="rounded-full bg-chat-accent/20 px-2 py-0.5 text-chat-accent">
            rota: {usage.route}
          </span>
        </div>
        <BreakdownBar items={breakdown} mode="tokens" />
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div>
        <h3 className="mb-3 text-sm font-medium text-white">Sessão</h3>
        <div className="grid grid-cols-2 gap-2">
          <div className="rounded-lg bg-chat-surface p-3">
            <p className="text-xs text-chat-muted">Total de tokens</p>
            <p className="text-lg font-semibold">{totalTokens.toLocaleString()}</p>
          </div>
          <div className="rounded-lg bg-chat-surface p-3">
            <p className="text-xs text-chat-muted">Créditos gastos</p>
            <p className="text-lg font-semibold">{totalCredits.toFixed(6)}</p>
          </div>
        </div>
      </div>

      {breakdown.length > 0 && (
        <>
          <div>
            <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-chat-muted">
              Distribuição de tokens
            </h3>
            <BreakdownBar items={breakdown} mode="tokens" />
          </div>
          <div>
            <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-chat-muted">
              Distribuição de créditos
            </h3>
            <BreakdownBar items={breakdown} mode="credits" />
          </div>
        </>
      )}

      {usage && (
        <div className="rounded-lg border border-chat-border p-3 text-xs text-chat-muted">
          <p>Local: {usage.tokens.local_total} tokens ({usage.tokens.local_input} in / {usage.tokens.local_output} out)</p>
          <p>Remoto: {usage.tokens.remote_total} tokens ({usage.tokens.remote_input} in / {usage.tokens.remote_output} out)</p>
        </div>
      )}
    </div>
  );
}