const API_BASE = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ?? "";

function apiUrl(path: string): string {
  return `${API_BASE}${path}`;
}

async function parseJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

import type {
  ChatApiResponse,
  HealthResponse,
  SchemesResponse,
} from "../types/chat";

export async function postChat(message: string): Promise<ChatApiResponse> {
  const response = await fetch(apiUrl("/api/chat"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  return parseJson<ChatApiResponse>(response);
}

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(apiUrl("/api/health"));
  return parseJson<HealthResponse>(response);
}

export async function getSchemes(): Promise<SchemesResponse> {
  const response = await fetch(apiUrl("/api/schemes"));
  return parseJson<SchemesResponse>(response);
}
