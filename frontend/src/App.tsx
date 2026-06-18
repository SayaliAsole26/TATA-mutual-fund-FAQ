import { useCallback, useEffect, useState } from "react";
import { getHealth } from "./api/client";
import Chat from "./components/Chat";
import ChatSidebar from "./components/ChatSidebar";
import Header from "./components/Header";
import { useChatSessions } from "./hooks/useChatSessions";
import type { ChatMessage, HealthResponse } from "./types/chat";

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
  const [apiStatus, setApiStatus] = useState<
    "checking" | "ok" | "unreachable" | "no_index" | "no_groq"
  >("checking");
  const [ingestInfo, setIngestInfo] = useState<HealthResponse["ingest"]>();

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;

    const applyHealth = (h: HealthResponse): boolean => {
      setIngestInfo(h.ingest);
      if (h.llm && !h.llm.configured) {
        setApiStatus("no_groq");
        return false;
      }
      if (h.status === "ok" || h.index?.status === "ok") {
        setApiStatus("ok");
        return false;
      }
      const indexStatus = h.index?.status;
      if (indexStatus === "empty" || indexStatus === "missing_collection") {
        setApiStatus("no_index");
        return h.ingest?.status === "running";
      }
      setApiStatus("unreachable");
      return true;
    };

    const poll = async () => {
      try {
        const h = await getHealth();
        if (cancelled) return;
        const keepPolling = applyHealth(h);
        if (keepPolling) {
          timer = setTimeout(poll, 5000);
        }
      } catch {
        if (!cancelled) {
          setApiStatus("unreachable");
          timer = setTimeout(poll, 10000);
        }
      }
    };

    poll();
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
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

        {apiStatus === "unreachable" && (
          <div className="mx-md mt-20 rounded-lg border border-error-container bg-error-container/20 px-md py-sm text-sm text-on-error-container">
            {import.meta.env.PROD ? (
              <>
                Cannot reach the backend API.
                {!import.meta.env.VITE_API_BASE_URL && (
                  <>
                    {" "}
                    <strong>VITE_API_BASE_URL</strong> was not set when this
                    site was built — add it in Vercel (e.g.{" "}
                    <code className="font-mono text-xs">
                      https://your-app.up.railway.app
                    </code>
                    ) and redeploy.
                  </>
                )}
                {import.meta.env.VITE_API_BASE_URL && (
                  <>
                    {" "}
                    Check that{" "}
                    <code className="font-mono text-xs">
                      {import.meta.env.VITE_API_BASE_URL.startsWith("http://")
                        ? import.meta.env.VITE_API_BASE_URL.replace(
                            "http://",
                            "https://",
                          )
                        : import.meta.env.VITE_API_BASE_URL}
                    </code>{" "}
                    is running (use <strong>https://</strong> on Vercel) and that
                    Railway <code className="font-mono text-xs">CORS_ORIGINS</code>{" "}
                    is{" "}
                    <code className="font-mono text-xs">
                      {typeof window !== "undefined"
                        ? window.location.origin
                        : "https://your-app.vercel.app"}
                    </code>{" "}
                    with no trailing slash.
                  </>
                )}
              </>
            ) : (
              <>
                API unavailable — run{" "}
                <code className="font-mono text-xs">
                  cd backend && uvicorn app.main:app --port 8000
                </code>
              </>
            )}
          </div>
        )}

        {apiStatus === "no_groq" && (
          <div className="mx-md mt-20 rounded-lg border border-error-container bg-error-container/20 px-md py-sm text-sm text-on-error-container">
            Groq LLM is not configured on the backend. Add{" "}
            <code className="font-mono text-xs">GROQ_API_KEY</code> in{" "}
            <strong>Railway</strong> (not Vercel), redeploy the API, then refresh.
            The key in your local <code className="font-mono text-xs">.env</code>{" "}
            is not copied to production automatically.
          </div>
        )}

        {apiStatus === "no_index" && (
          <div className="mx-md mt-20 rounded-lg border border-secondary-container bg-secondary-container/20 px-md py-sm text-sm text-on-surface">
            {ingestInfo?.status === "running" ? (
              <>
                Building the search index on Railway (
                {ingestInfo.mode === "embed_only"
                  ? "embedding bundled corpus"
                  : "fetching Groww pages"}
                ) — usually 3–10 minutes. This page will update automatically when
                the index is ready.
              </>
            ) : ingestInfo?.status === "failed" ? (
              <>
                Index build failed on Railway (exit {ingestInfo.exit_code}). Check
                Railway deploy logs, redeploy, or call{" "}
                <code className="font-mono text-xs">POST /api/ingest</code> with{" "}
                <code className="font-mono text-xs">INGEST_API_KEY</code>.
              </>
            ) : (
              <>
                Backend is online but the corpus index is missing. Wait for the
                automatic index build after redeploy, or trigger{" "}
                <code className="font-mono text-xs">POST /api/ingest</code>.
              </>
            )}
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
