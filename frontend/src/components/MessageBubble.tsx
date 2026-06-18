import type { ChatMessage } from "../types/chat";
import {
  formatTime,
  highlightAnswerHtml,
  parseFormattedAnswer,
} from "../utils/parseAnswer";

interface MessageBubbleProps {
  message: ChatMessage;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  if (message.role === "user") {
    return (
      <div className="flex flex-col items-end gap-xs animate-in fade-in">
        <div className="max-w-[85%] rounded-lg rounded-tr-none border border-outline-variant border-l-4 border-l-white bg-surface-variant px-md py-sm">
          <p className="text-base text-on-surface">{message.content}</p>
        </div>
        <span className="font-mono text-xs text-on-surface-variant">
          {formatTime(message.timestamp)}
        </span>
      </div>
    );
  }

  const isRefusal = message.responseType === "refusal";
  const isClarification = message.responseType === "clarification";
  const isError = message.responseType === "error";
  const parsed = parseFormattedAnswer(message.content);
  const sourceUrl = message.sourceUrl ?? parsed.sourceUrl;
  const lastUpdated = message.lastUpdated ?? parsed.lastUpdated;

  const borderClass = isRefusal
    ? "border-l-secondary-container"
    : isError
      ? "border-l-error"
      : isClarification
        ? "border-l-tertiary-container"
        : "border-l-primary-container";

  const label = isRefusal
    ? "Information only"
    : isError
      ? "Error"
      : isClarification
        ? "Clarification"
        : "Verified fact";

  const icon = isRefusal || isClarification ? "warning" : isError ? "report" : "auto_awesome";

  return (
    <div className="flex flex-col items-start gap-xs animate-in fade-in">
      <div
        className={`relative w-full overflow-hidden rounded-lg border border-outline-variant border-l-4 ${borderClass} bg-surface-container-high p-md shadow-md`}
      >
        <div className="mb-sm flex items-center gap-xs">
          <span
            className={`material-symbols-outlined text-[18px] ${
              isRefusal ? "text-secondary-container" : isError ? "text-error" : "text-primary"
            }`}
          >
            {icon}
          </span>
          <span
            className={`font-mono text-[10px] font-bold uppercase tracking-widest ${
              isRefusal ? "text-secondary-container" : isError ? "text-error" : "text-primary"
            }`}
          >
            {label}
          </span>
        </div>

        <div
          className="mb-md text-base leading-relaxed text-on-surface"
          dangerouslySetInnerHTML={{ __html: highlightAnswerHtml(parsed.body) }}
        />

        {sourceUrl && (
          <div className="mb-sm border-t border-outline-variant pt-sm">
            <a
              href={sourceUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-xs font-mono text-xs text-primary hover:underline"
            >
              <span className="material-symbols-outlined text-[16px]">link</span>
              View source
              <span className="material-symbols-outlined text-[14px]">open_in_new</span>
            </a>
          </div>
        )}

        {lastUpdated && (
          <p className="font-mono text-xs text-on-surface-variant opacity-70">
            Last updated: {lastUpdated}
          </p>
        )}
      </div>
      <span className="font-mono text-xs text-on-surface-variant">
        {formatTime(message.timestamp)}
      </span>
    </div>
  );
}
