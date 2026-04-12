import { platforms } from "@/lib/platforms";

interface Props {
  selected: string | null;
  onSelect: (id: string) => void;
  disabled?: boolean;
}

export function PlatformPicker({ selected, onSelect, disabled }: Props) {
  return (
    <div className="grid grid-cols-[repeat(auto-fill,minmax(130px,1fr))] gap-2">
      {platforms.map((p) => (
        <button
          key={p.id}
          className={`rounded-md border px-3 py-2.5 text-sm transition-all ${
            selected === p.id
              ? "border-transparent text-white"
              : "border-border bg-surface text-[#e5e5e5] hover:border-border-hover hover:bg-surface-hover"
          } disabled:cursor-not-allowed disabled:opacity-50`}
          style={
            selected === p.id
              ? { backgroundColor: p.colour, borderColor: p.colour }
              : {}
          }
          onClick={() => onSelect(p.id)}
          disabled={disabled}
        >
          {p.name}
        </button>
      ))}
    </div>
  );
}
