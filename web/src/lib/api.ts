import type { ApiResponse, ResolveResult } from "@/types/api";

const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  const json: ApiResponse<T> = await res.json();

  if (!res.ok || json.status === "error") {
    throw new Error(json.message || `Error ${res.status}`);
  }

  return json.data;
}

export const api = {
  links: {
    resolve: (url: string, targetPlatform: string) =>
      request<ResolveResult>("/api/resolve", {
        method: "POST",
        body: JSON.stringify({ url, target_platform: targetPlatform }),
      }),
  },
};
