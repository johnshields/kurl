import { useState } from "react";
import { api } from "@/lib/api";
import type { ResolveResult } from "@/types/api";
import { PlatformPicker } from "@/components/shared/PlatformPicker";
import { Result } from "@/components/shared/Result";

export default function ResolvePage() {
  const [url, setUrl] = useState("");
  const [platform, setPlatform] = useState<string | null>(null);
  const [result, setResult] = useState<ResolveResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleResolve() {
    if (!url.trim() || !platform) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await api.links.resolve(url.trim(), platform);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto flex max-w-[480px] flex-col gap-5 px-6 py-12">
      <h1 className="text-4xl font-bold tracking-tight">kurl</h1>
      <p className="text-sm text-muted">
        Paste a song link. Pick a platform. Done.
      </p>

      <input
        type="url"
        className="w-full rounded-lg border border-border bg-surface px-4 py-3 text-sm text-[#e5e5e5] outline-none transition-colors placeholder:text-[#555] focus:border-border-hover"
        placeholder="Paste a Spotify, Apple Music, YouTube Music link..."
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        disabled={loading}
      />

      <PlatformPicker
        selected={platform}
        onSelect={setPlatform}
        disabled={loading}
      />

      <button
        className="rounded-lg bg-[#e5e5e5] px-4 py-3 text-sm font-semibold text-[#0a0a0a] transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-30"
        onClick={handleResolve}
        disabled={!url.trim() || !platform || loading}
      >
        {loading ? "Resolving..." : "Resolve"}
      </button>

      {error && <p className="text-sm text-error">{error}</p>}
      {result && <Result result={result} />}
    </main>
  );
}
