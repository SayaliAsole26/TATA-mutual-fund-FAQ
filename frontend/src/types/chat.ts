export type ChatMessageRole = "user" | "assistant";

export type ChatResponseType =
  | "answer"
  | "clarification"
  | "refusal"
  | "error";

export interface ChatMessage {
  id: string;
  role: ChatMessageRole;
  content: string;
  responseType?: ChatResponseType;
  reason?: string;
  sourceUrl?: string;
  lastUpdated?: string;
  schemeName?: string;
  timestamp: number;
}

export interface ChatSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: number;
  updatedAt: number;
}

export interface ChatAnswerResponse {
  type: "answer";
  answer: string;
  scheme_id: string;
  scheme_name: string;
  source_url: string;
  last_updated?: string | null;
  sections_used?: string[];
  retrieval_source?: string;
}

export interface ChatClarificationResponse {
  type: "clarification";
  message: string;
  schemes: string[];
}

export interface ChatRefusalResponse {
  type: "refusal";
  reason: string;
  answer: string;
  source_url: string;
  scheme_name?: string;
}

export interface ChatErrorResponse {
  type: "error";
  message: string;
}

export type ChatApiResponse =
  | ChatAnswerResponse
  | ChatClarificationResponse
  | ChatRefusalResponse
  | ChatErrorResponse;

export interface SchemeItem {
  scheme_id: string;
  scheme_name: string;
  source_url: string;
  category: string;
}

export interface SchemesResponse {
  amc: string;
  schemes: SchemeItem[];
}

export interface HealthResponse {
  status: string;
  index: Record<string, unknown>;
  corpus?: {
    status: string;
    age_hours?: number;
    stale_after_hours?: number;
  };
  llm?: {
    provider: string;
    configured: boolean;
    model: string;
  };
  issues?: string[];
  ingest?: {
    status: string;
    mode?: string;
    started_at?: string;
    finished_at?: string;
    exit_code?: number;
    error?: string;
  };
}
