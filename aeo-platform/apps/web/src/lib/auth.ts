import { cookies } from "next/headers";

export const AUTH_COOKIE = "aeo_session";
const COOKIE_MAX_AGE = 60 * 60 * 24 * 7;

export function getSessionToken(): string | undefined {
  const cookieStore = cookies();
  return cookieStore.get(AUTH_COOKIE)?.value;
}

export function getAccessToken(): string | undefined {
  const raw = getSessionToken();
  if (!raw) return undefined;
  const session = parseSessionCookie(raw);
  return session?.access_token;
}

export function decodeJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;
    const payload = Buffer.from(parts[1]!, "base64url").toString("utf-8");
    return JSON.parse(payload) as Record<string, unknown>;
  } catch {
    return null;
  }
}

export function isTokenExpired(token: string): boolean {
  const payload = decodeJwtPayload(token);
  if (!payload || typeof payload.exp !== "number") return true;
  return payload.exp < Math.floor(Date.now() / 1000);
}

export function buildSessionCookie(accessToken: string, refreshToken: string): string {
  return JSON.stringify({ access_token: accessToken, refresh_token: refreshToken });
}

export function parseSessionCookie(
  value: string
): { access_token: string; refresh_token: string } | null {
  try {
    const parsed = JSON.parse(value) as { access_token: string; refresh_token: string };
    if (parsed.access_token && parsed.refresh_token) return parsed;
    return null;
  } catch {
    return null;
  }
}

export const SESSION_COOKIE_OPTIONS = {
  httpOnly: true,
  secure: process.env.NODE_ENV === "production",
  sameSite: "lax" as const,
  path: "/",
  maxAge: COOKIE_MAX_AGE,
};
