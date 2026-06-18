export interface ParsedAnswer {
  body: string;
  sourceUrl: string | null;
  lastUpdated: string | null;
}

/** Split API formatted answer into body + metadata (source below, not inline). */
export function parseFormattedAnswer(answer: string): ParsedAnswer {
  const sourceIdx = answer.search(/\n\nSource:\s*/i);
  if (sourceIdx === -1) {
    return { body: answer.trim(), sourceUrl: null, lastUpdated: null };
  }

  const body = answer.slice(0, sourceIdx).trim();
  const tail = answer.slice(sourceIdx);
  const sourceMatch = tail.match(/Source:\s*(.+)/i);
  const footerMatch = tail.match(/Last updated from sources:\s*(.+)/i);

  return {
    body,
    sourceUrl: sourceMatch?.[1]?.trim() ?? null,
    lastUpdated: footerMatch?.[1]?.trim() ?? null,
  };
}

/** Highlight ₹ amounts, percentages, and key numerics in answer body. */
export function highlightAnswerHtml(body: string): string {
  const escaped = body
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  return escaped
    .replace(/(₹[\d,]+(?:\.\d+)?)/g, '<span class="highlight-fact">$1</span>')
    .replace(/(\d+(?:\.\d+)?%)/g, '<span class="highlight-fact">$1</span>')
    .replace(/\b(Tata[\w\s&]+?(?:Fund|Growth|Direct|Plan|Index)[\w\s]*)/gi, (m) =>
      m.length > 8 ? `<span class="highlight-fact">${m}</span>` : m,
    );
}

export function sessionTitleFromMessage(message: string): string {
  const trimmed = message.trim();
  if (trimmed.length <= 42) return trimmed;
  return `${trimmed.slice(0, 42)}…`;
}

export function formatTime(ts: number): string {
  return new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}
