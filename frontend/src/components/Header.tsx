interface HeaderProps {
  onToggleSessions: () => void;
  sessionsOpen: boolean;
}

export default function Header({ onToggleSessions, sessionsOpen }: HeaderProps) {
  return (
    <header className="fixed top-0 z-50 flex h-16 w-full items-center border-b border-outline-variant bg-surface px-md">
      <div className="mx-auto flex w-full max-w-container-max items-center gap-sm">
        <span className="material-symbols-outlined text-primary">account_balance</span>
        <div className="min-w-0 flex-1">
          <h1 className="truncate text-lg font-bold text-on-surface">
            Mutual Fund FAQ Assistant
          </h1>
          <p className="truncate font-mono text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
            Powered by Groww · Facts-only
          </p>
        </div>
        <button
          type="button"
          onClick={onToggleSessions}
          className="rounded-full p-sm transition-colors hover:bg-surface-variant"
          aria-label="Toggle chat sessions"
          aria-expanded={sessionsOpen}
        >
          <span className="material-symbols-outlined text-on-surface-variant">
            {sessionsOpen ? "close" : "forum"}
          </span>
        </button>
      </div>
    </header>
  );
}
