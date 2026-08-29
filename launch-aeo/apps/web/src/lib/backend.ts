const API_BASE_URL = process.env.API_BASE_URL ?? "http://127.0.0.1:8000";
const AUTH_API_KEY = process.env.AUTH_API_KEY ?? "dev-api-key-change-in-production";

type FetchOptions = {
  method?: "GET" | "POST";
  body?: unknown;
};

export async function backendFetch<T>(path: string, options: FetchOptions = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method ?? "GET",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${AUTH_API_KEY}`,
    },
    body: options.body ? JSON.stringify(options.body) : undefined,
    cache: "no-store",
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`API ${response.status}: ${text}`);
  }

  const payload = (await response.json()) as { code: number; message: string; data: T };
  if (payload.code !== 0) {
    throw new Error(payload.message || "API request failed");
  }

  return payload.data;
}
