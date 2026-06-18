const EXAMPLES = [
  "What is the minimum SIP for Tata ELSS?",
  "What is the exit load on Tata Silver ETF FoF?",
  "Who manages the Tata Flexi Cap Fund?",
];

interface ExampleChipsProps {
  onSelect: (question: string) => void;
  disabled?: boolean;
}

export default function ExampleChips({ onSelect, disabled }: ExampleChipsProps) {
  return (
    <div className="flex flex-wrap justify-center gap-sm py-md">
      {EXAMPLES.map((q) => (
        <button
          key={q}
          type="button"
          disabled={disabled}
          onClick={() => onSelect(q)}
          className="rounded-full border border-outline-variant bg-surface-container px-md py-sm font-mono text-xs text-on-surface-variant transition-all hover:border-primary hover:text-primary active:scale-95 disabled:opacity-50"
        >
          {q}
        </button>
      ))}
    </div>
  );
}
