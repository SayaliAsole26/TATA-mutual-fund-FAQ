import { useCallback, useEffect, useState } from "react";
import type { ChatMessage, ChatSession } from "../types/chat";
import { sessionTitleFromMessage } from "../utils/parseAnswer";

const STORAGE_KEY = "tata-mf-faq-sessions";
const ACTIVE_KEY = "tata-mf-faq-active-session";

function newId(): string {
  return crypto.randomUUID();
}

function createSession(): ChatSession {
  const now = Date.now();
  return {
    id: newId(),
    title: "New chat",
    messages: [],
    createdAt: now,
    updatedAt: now,
  };
}

function loadSessions(): ChatSession[] {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return [createSession()];
    const parsed = JSON.parse(raw) as ChatSession[];
    return parsed.length ? parsed : [createSession()];
  } catch {
    return [createSession()];
  }
}

function loadActiveId(sessions: ChatSession[]): string {
  const stored = sessionStorage.getItem(ACTIVE_KEY);
  if (stored && sessions.some((s) => s.id === stored)) return stored;
  return sessions[0].id;
}

export function useChatSessions() {
  const [sessions, setSessions] = useState<ChatSession[]>(loadSessions);
  const [activeId, setActiveId] = useState<string>(() =>
    loadActiveId(loadSessions()),
  );

  const activeSession =
    sessions.find((s) => s.id === activeId) ?? sessions[0] ?? createSession();

  useEffect(() => {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
  }, [sessions]);

  useEffect(() => {
    sessionStorage.setItem(ACTIVE_KEY, activeId);
  }, [activeId]);

  const createNewChat = useCallback(() => {
    const session = createSession();
    setSessions((prev) => [session, ...prev]);
    setActiveId(session.id);
  }, []);

  const deleteChat = useCallback(
    (id: string) => {
      setSessions((prev) => {
        const next = prev.filter((s) => s.id !== id);
        if (next.length === 0) {
          const fresh = createSession();
          setActiveId(fresh.id);
          return [fresh];
        }
        if (id === activeId) {
          setActiveId(next[0].id);
        }
        return next;
      });
    },
    [activeId],
  );

  const appendMessage = useCallback(
    (sessionId: string, message: ChatMessage, firstUserText?: string) => {
      setSessions((prev) =>
        prev.map((s) => {
          if (s.id !== sessionId) return s;
          const title =
            s.title === "New chat" && firstUserText
              ? sessionTitleFromMessage(firstUserText)
              : s.title;
          return {
            ...s,
            title,
            messages: [...s.messages, message],
            updatedAt: Date.now(),
          };
        }),
      );
    },
    [],
  );

  return {
    sessions,
    activeSession,
    activeId,
    setActiveId,
    createNewChat,
    deleteChat,
    appendMessage,
  };
}
