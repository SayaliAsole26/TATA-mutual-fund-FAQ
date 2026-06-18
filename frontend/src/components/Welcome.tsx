interface WelcomeProps {
  onExample: (q: string) => void;
  disabled?: boolean;
}

export default function Welcome({ onExample, disabled }: WelcomeProps) {
  return (
    <div className="rounded-lg border border-outline-variant bg-surface-container p-lg text-center">
      <span className="material-symbols-outlined mb-sm text-3xl text-primary">
        auto_awesome
      </span>
      <h2 className="mb-sm text-xl font-semibold text-on-surface">
        Tata Mutual Fund FAQ
      </h2>
      <p className="mb-lg text-sm leading-relaxed text-on-surface-variant">
        Ask objective questions about 15 Tata Mutual Fund schemes on Groww — expense
        ratio, minimum SIP, exit load, fund managers, benchmark, and more. I provide
        brief, verified facts with a source link below each answer.
      </p>
      <ExampleChipsInline onSelect={onExample} disabled={disabled} />
    </div>
  );
}

function ExampleChipsInline({
  onSelect,
  disabled,
}: {
  onSelect: (q: string) => void;
  disabled?: boolean;
}) {
  const items = [
    "Minimum SIP for Tata ELSS?",
    "Exit load on Tata Silver ETF FoF?",
    "Who manages Tata Flexi Cap?",
  ];
  return (
    <div className="flex flex-col gap-sm">
      {items.map((q) => (
        <button
          key={q}
          type="button"
          disabled={disabled}
          onClick={() => onSelect(q)}
          className="rounded-lg border border-outline-variant bg-surface-container-high px-md py-sm text-left text-sm text-on-surface transition-colors hover:border-primary disabled:opacity-50"
        >
          {q}
        </button>
      ))}
    </div>
  );
}
