export default function Disclaimer() {
  return (
    <div className="border-l-4 border-secondary-container bg-secondary-container/10 p-sm backdrop-blur-md">
      <div className="flex items-start gap-sm">
        <span className="material-symbols-outlined text-[18px] text-secondary-container">
          warning
        </span>
        <p className="font-mono text-xs text-on-surface opacity-90">
          Facts-only. No investment advice. Mutual fund investments are subject to
          market risks. Read all scheme related documents carefully.
        </p>
      </div>
    </div>
  );
}
