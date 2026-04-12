export interface ApiResponse<T> {
  status: "success" | "error";
  message: string;
  data: T;
}

export interface ResolveResult {
  title: string | null;
  artist: string | null;
  resolved_url: string;
  platform: string;
  cached: boolean;
}
