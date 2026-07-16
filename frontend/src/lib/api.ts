export const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function api(path: string, opts: RequestInit = {}) {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  const res = await fetch(`${API}${path}`, {
    ...opts,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(opts.headers ?? {}),
    },
  });
  if (res.status === 401 && typeof window !== "undefined" && !path.startsWith("/auth")) {
    // expired/invalid token → back to login
    localStorage.clear();
    window.location.href = "/login";
    throw new Error("Session expired");
  }
  if (!res.ok) {
    const b = await res.json().catch(() => ({}));
    throw new Error(b?.detail ?? `HTTP ${res.status}`);
  }
  return res.status === 204 ? null : res.json();
}

export function roleFromToken(): string | null {
  const t = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  if (!t) return null;
  try { return JSON.parse(atob(t.split(".")[1])).role ?? null; } catch { return null; }
}
