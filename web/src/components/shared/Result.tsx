import type { ResolveResult } from "@/types/api";

interface Props {
  result: ResolveResult;
}

export function Result({ result }: Props) {
  return (
    <div className="flex flex-col gap-2 rounded-lg border border-border bg-surface p-4">
      <p className="text-sm">
        {result.artist && <span className="text-muted">{result.artist}</span>}
        {result.artist && result.title && " — "}
        {result.title && <span className="font-semibold">{result.title}</span>}
      </p>
      <a
        href={result.resolved_url}
        target="_blank"
        rel="noopener noreferrer"
        className="rounded-md bg-[#222] px-3 py-2 text-center text-sm font-medium text-[#e5e5e5] no-underline transition-colors hover:bg-[#333]"
      >
        Open on {result.platform}
      </a>
      {result.cached && (
        <span className="self-end text-xs text-[#555]">cached</span>
      )}
    </div>
  );
}
