import type { ChatSession } from "../types/chat";
import { formatTime } from "../utils/parseAnswer";

interface ChatSidebarProps {
  sessions: ChatSession[];
  activeId: string;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
  onClose: () => void;
  desktop?: boolean;
}

export default function ChatSidebar({
  sessions,
  activeId,
  onSelect,
  onNew,
  onDelete,
  onClose,
  desktop = false,
}: ChatSidebarProps) {
  if (desktop) {
    return (
      <div className="flex flex-1 flex-col bg-surface-container-low">
        <SidebarContent
          sessions={sessions}
          activeId={activeId}
          onSelect={onSelect}
          onNew={onNew}
          onDelete={onDelete}
          onClose={onClose}
          showClose={false}
        />
      </div>
    );
  }

  return (
    <aside className="fixed inset-0 z-[60] flex md:hidden">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} aria-hidden />
      <div className="relative ml-auto flex h-full w-[min(100%,20rem)] flex-col bg-surface-container-low shadow-xl">
        <SidebarContent
          sessions={sessions}
          activeId={activeId}
          onSelect={onSelect}
          onNew={onNew}
          onDelete={onDelete}
          onClose={onClose}
          showClose
        />
      </div>
    </aside>
  );
}

function SidebarContent({
  sessions,
  activeId,
  onSelect,
  onNew,
  onDelete,
  onClose,
  showClose,
}: Omit<ChatSidebarProps, "desktop"> & { showClose: boolean }) {
  return (
    <>
      <div className="flex items-center justify-between border-b border-outline-variant p-md">
        <h2 className="font-mono text-xs font-bold uppercase tracking-wider text-on-surface-variant">
          Chats
        </h2>
        {showClose && (
          <button
            type="button"
            onClick={onClose}
            className="rounded p-xs"
            aria-label="Close"
          >
            <span className="material-symbols-outlined">close</span>
          </button>
        )}
      </div>
      <button
        type="button"
        onClick={onNew}
        className="m-md flex items-center justify-center gap-xs rounded-lg border border-primary bg-primary/10 py-sm font-mono text-xs font-medium text-primary transition-colors hover:bg-primary/20"
      >
        <span className="material-symbols-outlined text-[18px]">add</span>
        New chat
      </button>
      <ul className="custom-scroll flex-1 overflow-y-auto px-sm pb-md">
        {sessions.map((s) => (
          <li key={s.id} className="mb-xs">
            <div
              className={`group flex items-center gap-xs rounded-lg border px-sm py-sm transition-colors ${
                s.id === activeId
                  ? "border-primary bg-surface-container-high"
                  : "border-transparent hover:border-outline-variant hover:bg-surface-container"
              }`}
            >
              <button
                type="button"
                className="min-w-0 flex-1 text-left"
                onClick={() => {
                  onSelect(s.id);
                  onClose();
                }}
              >
                <p className="truncate text-sm text-on-surface">{s.title}</p>
                <p className="font-mono text-[10px] text-on-surface-variant">
                  {formatTime(s.updatedAt)} · {s.messages.length} msgs
                </p>
              </button>
              <button
                type="button"
                onClick={() => onDelete(s.id)}
                className="rounded p-xs opacity-0 transition-opacity hover:bg-surface-variant group-hover:opacity-100"
                aria-label={`Delete ${s.title}`}
              >
                <span className="material-symbols-outlined text-[18px] text-error">
                  delete
                </span>
              </button>
            </div>
          </li>
        ))}
      </ul>
    </>
  );
}
