import type {
  ChatApiResponse,
  HealthResponse,
  SchemesResponse,
} from "../types/chat";

function normalizeApiBase(raw: string | undefined): string {
  const trimmed = raw?.trim().replace(/\/$/, "") ?? "";
  if (!trimmed) return "";

  // Vercel is HTTPS — calling http://railway URLs is blocked as mixed content.
  if (import.meta.env.PROD && trimmed.startsWith("http://")) {
    return `https://${trimmed.slice("http://".length)}`;
  }
  return trimmed;
}

const API_BASE = normalizeApiBase(import.meta.env.VITE_API_BASE_URL);

function apiUrl(path: string): string {
  if (!API_BASE) {
    throw new Error(
      "VITE_API_BASE_URL is not configured. Set it in Vercel and redeploy the frontend.",
    );
  }
  return `${API_BASE}${path}`;
}

function messageFromErrorBody(text: string, status: number): string {
  try {
    const body = JSON.parse(text) as {
      type?: string;
      message?: string;
      detail?: string | { msg?: string }[];
    };
    if (body.type === "error" && body.message) {
      return body.message;
    }
    if (typeof body.detail === "string") {
      return body.detail;
    }
    if (Array.isArray(body.detail) && body.detail[0]?.msg) {
      return body.detail[0].msg;
    }
  } catch {
    // not JSON
  }
  if (status === 429) {
    return "Too many requests. Please wait a minute and try again.";
  }
  if (status >= 500) {
    return "The API returned a server error. Try again in a moment.";
  }
  return text || `Request failed (${status})`;
}

export function friendlyApiError(err: unknown): string {
  if (err instanceof Error) {
    if (err.message.includes("Failed to fetch") || err.message.includes("NetworkError")) {
      return (
        "Could not reach the API. Check that the backend is running, " +
        "VITE_API_BASE_URL is set on Vercel, and CORS_ORIGINS on Railway includes your site URL."
      );
    }
    return err.message;
  }
  return "Could not reach the assistant. Please try again.";
}

async function parseJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const text = await response.text();
    throw new Error(messageFromErrorBody(text, response.status));
  }
  return response.json() as Promise<T>;
}

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
