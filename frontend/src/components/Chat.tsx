import { useCallback, useEffect, useRef, useState } from "react";
import { postChat } from "../api/client";
import type { ChatApiResponse, ChatMessage } from "../types/chat";
import { parseFormattedAnswer } from "../utils/parseAnswer";
import ExampleChips from "./ExampleChips";
import Disclaimer from "./Disclaimer";
import InputBar from "./InputBar";
import MessageBubble from "./MessageBubble";
import Welcome from "./Welcome";

interface ChatProps {
  messages: ChatMessage[];
  onAppend: (msg: ChatMessage, firstUserText?: string) => void;
}

function apiToAssistantMessage(res: ChatApiResponse): ChatMessage {
  const base = {
    id: crypto.randomUUID(),
    role: "assistant" as const,
    timestamp: Date.now(),
  };

  if (res.type === "answer") {
    const parsed = parseFormattedAnswer(res.answer);
    return {
      ...base,
      content: res.answer,
      responseType: "answer",
      sourceUrl: res.source_url ?? parsed.sourceUrl ?? undefined,
      lastUpdated: parsed.lastUpdated ?? undefined,
      schemeName: res.scheme_name,
    };
  }
  if (res.type === "refusal") {
    const parsed = parseFormattedAnswer(res.answer);
    return {
      ...base,
      content: res.answer,
      responseType: "refusal",
      reason: res.reason,
      sourceUrl: res.source_url ?? parsed.sourceUrl ?? undefined,
      lastUpdated: parsed.lastUpdated ?? undefined,
      schemeName: res.scheme_name,
    };
  }
  if (res.type === "clarification") {
    return {
      ...base,
      content: res.message,
      responseType: "clarification",
    };
  }
  return {
    ...base,
    content: res.message,
    responseType: "error",
  };
}

export default function Chat({ messages, onAppend }: ChatProps) {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || loading) return;

      const userMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content: trimmed,
        timestamp: Date.now(),
      };
      const isFirst = messages.length === 0;
      onAppend(userMsg, isFirst ? trimmed : undefined);
      setInput("");
      setError(null);
      setLoading(true);

      try {
        const res = await postChat(trimmed);
        onAppend(apiToAssistantMessage(res));
      } catch (err) {
        const msg =
          err instanceof Error
            ? err.message
            : "Could not reach the assistant. Please try again.";
        setError(msg);
        onAppend({
          id: crypto.randomUUID(),
          role: "assistant",
          content:
            "I could not connect to the server right now. Please check that the API is running and try again.",
          responseType: "error",
          timestamp: Date.now(),
        });
      } finally {
        setLoading(false);
      }
    },
    [loading, messages.length, onAppend],
  );

  return (
    <>
      <div className="custom-scroll flex-1 space-y-xl overflow-y-auto pb-52">
        {messages.length === 0 ? (
          <Welcome onExample={sendMessage} disabled={loading} />
        ) : (
          messages.map((m) => <MessageBubble key={m.id} message={m} />)
        )}
        {loading && (
          <div className="flex items-center gap-sm text-on-surface-variant">
            <span className="material-symbols-outlined animate-spin text-primary">
              progress_activity
            </span>
            <span className="font-mono text-xs">Fetching verified facts…</span>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="fixed bottom-0 left-0 right-0 z-50 border-t border-outline-variant bg-surface-container-low p-md md:left-72">
        <div className="mx-auto max-w-container-max space-y-sm">
          <Disclaimer />
          {messages.length > 0 && (
            <ExampleChips onSelect={sendMessage} disabled={loading} />
          )}
          {error && (
            <div className="rounded-lg border border-error-container bg-error-container/20 p-sm text-sm text-error">
              {error}
            </div>
          )}
          <InputBar
            value={input}
            onChange={setInput}
            onSubmit={() => sendMessage(input)}
            loading={loading}
          />
        </div>
      </div>
    </>
  );
}
