import { useCallback, useEffect, useState } from "react";
import { getHealth } from "./api/client";
import Chat from "./components/Chat";
import ChatSidebar from "./components/ChatSidebar";
import Header from "./components/Header";
import { useChatSessions } from "./hooks/useChatSessions";
import type { ChatMessage } from "./types/chat";

export default function App() {
  const {
    sessions,
    activeSession,
    activeId,
    setActiveId,
    createNewChat,
    deleteChat,
    appendMessage,
  } = useChatSessions();

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [apiStatus, setApiStatus] = useState<"checking" | "ok" | "degraded">(
    "checking",
  );

  useEffect(() => {
    getHealth()
      .then((h) => setApiStatus(h.status === "ok" ? "ok" : "degraded"))
      .catch(() => setApiStatus("degraded"));
  }, []);

  const handleAppend = useCallback(
    (msg: ChatMessage, firstUserText?: string) => {
      appendMessage(activeSession.id, msg, firstUserText);
    },
    [activeSession.id, appendMessage],
  );

  return (
    <div className="flex min-h-screen bg-surface text-on-surface">
      <div className="hidden md:flex md:w-72 md:flex-shrink-0 md:flex-col md:border-r md:border-outline-variant">
        <div className="h-16 flex-shrink-0" />
        <ChatSidebar
          sessions={sessions}
          activeId={activeId}
          onSelect={setActiveId}
          onNew={createNewChat}
          onDelete={deleteChat}
          onClose={() => undefined}
          desktop
        />
      </div>

      {sidebarOpen && (
        <ChatSidebar
          sessions={sessions}
          activeId={activeId}
          onSelect={setActiveId}
          onNew={() => {
            createNewChat();
            setSidebarOpen(false);
          }}
          onDelete={deleteChat}
          onClose={() => setSidebarOpen(false)}
        />
      )}

      <div className="flex min-h-screen min-w-0 flex-1 flex-col">
        <Header
          onToggleSessions={() => setSidebarOpen((o) => !o)}
          sessionsOpen={sidebarOpen}
        />

        {apiStatus === "degraded" && (
          <div className="mx-md mt-20 rounded-lg border border-error-container bg-error-container/20 px-md py-sm text-sm text-on-error-container">
            API unavailable — run{" "}
            <code className="font-mono text-xs">
              cd backend && uvicorn app.main:app --port 8000
            </code>
          </div>
        )}

        <main className="mx-auto flex w-full max-w-container-max flex-1 flex-col px-md pt-20">
          <Chat
            key={activeSession.id}
            messages={activeSession.messages}
            onAppend={handleAppend}
          />
        </main>
      </div>
    </div>
  );
}
