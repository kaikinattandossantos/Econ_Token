import { useRef, useEffect, type KeyboardEvent } from "react";

interface InputBarProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  disabled?: boolean;
}

export default function InputBar({ value, onChange, onSubmit, disabled }: InputBarProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }, [value]);

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!disabled && value.trim()) onSubmit();
    }
  };

  return (
    <div className="border-t border-chat-border bg-chat-bg px-4 pb-6 pt-4">
      <div className="mx-auto max-w-3xl">
        <div className="relative flex items-end rounded-2xl border border-chat-border bg-chat-surface shadow-lg">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Envie uma mensagem..."
            disabled={disabled}
            rows={1}
            className="max-h-[200px] min-h-[52px] flex-1 resize-none bg-transparent px-4 py-3.5 text-[15px] text-white placeholder:text-chat-muted focus:outline-none disabled:opacity-50"
          />
          <button
            onClick={onSubmit}
            disabled={disabled || !value.trim()}
            className="m-2 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white text-black transition hover:bg-gray-200 disabled:cursor-not-allowed disabled:opacity-30"
            aria-label="Enviar"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 19V5M5 12l7-7 7 7" />
            </svg>
          </button>
        </div>
        <p className="mt-2 text-center text-xs text-chat-muted">
          Router Agent roteia entre modelo local e remoto para economizar créditos
        </p>
      </div>
    </div>
  );
}