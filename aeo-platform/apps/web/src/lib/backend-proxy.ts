export function getBackendUrl(): string {
  return process.env.API_BASE_URL ?? "http://127.0.0.1:8000";
}

export function getAuthApiKey(): string {
  return process.env.AUTH_API_KEY ?? "dev-api-key-change-in-production";
}
