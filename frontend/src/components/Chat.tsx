import { useEffect, useRef } from "react";
import type { Message as MessageType } from "../types";
import Message from "./Message";
import InputBar from "./InputBar";

interface ChatProps {
  messages: MessageType[];
  input: string;
  onInputChange: (value: string) => void;
  onSubmit: () => void;
  isLoading: boolean;
}

export default function Chat({ messages, input, onInputChange, onSubmit, isLoading }: ChatProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex min-w-0 flex-1 flex-col">
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center px-4 text-center">
            <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-chat-surface text-2xl">
              R
            </div>
            <h1 className="mb-2 text-2xl font-semibold">Como posso ajudar?</h1>
            <p className="max-w-md text-sm text-chat-muted">
              Pergunte qualquer coisa. O agente decide automaticamente se usa o modelo local (grátis)
              ou remoto (créditos), e mostra o consumo de tokens em cada resposta.
            </p>
          </div>
        ) : (
          messages.map((msg) => <Message key={msg.id} message={msg} />)
        )}
        <div ref={bottomRef} />
      </div>

      <InputBar
        value={input}
        onChange={onInputChange}
        onSubmit={onSubmit}
        disabled={isLoading}
      />
    </div>
  );
}