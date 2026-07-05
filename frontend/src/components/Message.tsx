import ReactMarkdown from "react-markdown";
import type { Message as MessageType } from "../types";
import TokenPanel from "./TokenPanel";

interface MessageProps {
  message: MessageType;
}

export default function Message({ message }: MessageProps) {
  const isUser = message.role === "user";

  return (
    <div className={`group w-full ${isUser ? "bg-transparent" : "bg-chat-bg"}`}>
      <div className="mx-auto flex max-w-3xl gap-4 px-4 py-6 md:px-6">
        <div
          className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-sm text-sm font-medium ${
            isUser ? "bg-indigo-600" : "bg-chat-accent"
          }`}
        >
          {isUser ? "V" : "R"}
        </div>

        <div className="min-w-0 flex-1">
          {message.isLoading ? (
            <div className="flex items-center gap-1.5 py-2">
              <span className="h-2 w-2 animate-bounce rounded-full bg-chat-muted [animation-delay:-0.3s]" />
              <span className="h-2 w-2 animate-bounce rounded-full bg-chat-muted [animation-delay:-0.15s]" />
              <span className="h-2 w-2 animate-bounce rounded-full bg-chat-muted" />
            </div>
          ) : (
            <div className="prose-chat text-[15px] leading-7 text-gray-100">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          )}

          {!isUser && message.usage && !message.isLoading && (
            <TokenPanel usage={message.usage} compact />
          )}
        </div>
      </div>
    </div>
  );
}