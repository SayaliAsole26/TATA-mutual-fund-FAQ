export interface ParsedAnswer {
  body: string;
  sourceUrl: string | null;
  lastUpdated: string | null;
}

const SOURCE_MARKER = /\sSource:\s*/i;
const SOURCE_URL = /Source:\s*(https?:\/\/\S+)/i;
const LAST_UPDATED =
  /Last updated(?: from sources)?:\s*([^\n]+?)(?:\s*$|\s*Source:)/i;
const LAST_UPDATED_INLINE = /Last updated(?: from sources)?:\s*(.+?)$/i;

/** Strip markdown bold markers before rendering. */
export function stripMarkdownBold(text: string): string {
  return text.replace(/\*\*([^*]+)\*\*/g, "$1");
}

function normalizeBody(body: string): string {
  return stripMarkdownBold(body).replace(/\s+/g, " ").trim();
}

function extractLastUpdated(text: string): { text: string; lastUpdated: string | null } {
  const match =
    text.match(LAST_UPDATED) ?? text.match(LAST_UPDATED_INLINE);
  if (!match) return { text, lastUpdated: null };
  const lastUpdated = match[1].trim().replace(/\.$/, "");
  return { text: text.replace(match[0], "").trim(), lastUpdated };
}

function extractSource(text: string): { body: string; sourceUrl: string | null } {
  const doubleNlIdx = text.search(/\n\nSource:\s*/i);
  if (doubleNlIdx !== -1) {
    const body = text.slice(0, doubleNlIdx).trim();
    const tail = text.slice(doubleNlIdx);
    const urlMatch = tail.match(SOURCE_URL);
    return { body, sourceUrl: urlMatch?.[1]?.trim() ?? null };
  }

  const singleNlIdx = text.search(/\nSource:\s*/i);
  if (singleNlIdx !== -1) {
    const body = text.slice(0, singleNlIdx).trim();
    const tail = text.slice(singleNlIdx);
    const urlMatch = tail.match(SOURCE_URL);
    return { body, sourceUrl: urlMatch?.[1]?.trim() ?? null };
  }

  const inlineIdx = text.search(SOURCE_MARKER);
  if (inlineIdx !== -1) {
    const body = text.slice(0, inlineIdx).trim();
    const tail = text.slice(inlineIdx);
    const urlMatch = tail.match(SOURCE_URL);
    return { body, sourceUrl: urlMatch?.[1]?.trim() ?? null };
  }

  return { body: text, sourceUrl: null };
}

/** Split API formatted answer into body + metadata (source below, not inline). */
export function parseFormattedAnswer(answer: string): ParsedAnswer {
  const withoutFooter = extractLastUpdated(answer.trim());
  const { body, sourceUrl } = extractSource(withoutFooter.text);

  return {
    body: normalizeBody(body),
    sourceUrl,
    lastUpdated: withoutFooter.lastUpdated,
  };
}

/** Format ISO or human date for footer display. */
export function formatLastUpdated(raw: string | null | undefined): string | null {
  if (!raw?.trim()) return null;
  const trimmed = raw.trim();
  const parsed = new Date(trimmed);
  if (!Number.isNaN(parsed.getTime()) && /^\d{4}-\d{2}-\d{2}/.test(trimmed)) {
    return parsed.toLocaleDateString("en-GB", {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
  }
  return trimmed.replace(/\.$/, "");
}

/** Highlight ₹ amounts, percentages, and key numerics in answer body. */
export function highlightAnswerHtml(body: string): string {
  const cleaned = stripMarkdownBold(body);
  const escaped = cleaned
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  return escaped
    .replace(/(₹[\d,]+(?:\.\d+)?)/g, '<span class="highlight-fact">$1</span>')
    .replace(/(\d+(?:\.\d+)?%)/g, '<span class="highlight-fact">$1</span>')
    .replace(/\b(Tata[\w\s&]+?(?:Fund|Growth|Direct|Plan|Index|FoF)[\w\s]*)/gi, (m) =>
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
