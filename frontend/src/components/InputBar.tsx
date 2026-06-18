import type { KeyboardEvent } from "react";

interface InputBarProps {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  loading?: boolean;
  disabled?: boolean;
  placeholder?: string;
}

export default function InputBar({
  value,
  onChange,
  onSubmit,
  loading,
  disabled = false,
  placeholder = "Ask about fund details...",
}: InputBarProps) {
  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSubmit();
    }
  };

  return (
    <div className="flex items-center gap-sm rounded-full border border-outline-variant bg-surface-container-high p-xs transition-all focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/20">
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={loading || disabled}
        placeholder={
          disabled ? "Waiting for search index to finish building…" : placeholder
        }
        className="flex-grow border-none bg-transparent px-sm text-base text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:ring-0 disabled:opacity-60"
        aria-label="Chat message"
      />
      <button
        type="button"
        onClick={onSubmit}
        disabled={loading || disabled || !value.trim()}
        className="flex items-center justify-center rounded-full bg-primary p-sm text-on-primary shadow-lg transition-transform active:scale-95 disabled:opacity-40"
        aria-label="Send message"
      >
        <span
          className="material-symbols-outlined"
          style={{ fontVariationSettings: "'FILL' 1" }}
        >
          {loading ? "hourglass_top" : "send"}
        </span>
      </button>
    </div>
  );
}
