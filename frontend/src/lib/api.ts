// API base: explicit env override wins; otherwise talk to port 8000 on the SAME host the
// page was loaded from — so phones on the LAN (http://192.168.x.x:3000) reach the backend.
export const API =
  process.env.NEXT_PUBLIC_API_URL ??
  (typeof window !== "undefined" ? `http://${window.location.hostname}:8000` : "http://localhost:8000");

// "Keep me logged in" → localStorage (survives browser restart); otherwise sessionStorage (tab session only).
export function getToken(key = "access_token"): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(key) ?? sessionStorage.getItem(key);
}

export function setTokens(access: string, refresh: string, remember?: boolean) {
  const keep = remember ?? localStorage.getItem("remember") === "1"; // read before clearing
  clearTokens();
  const store = keep ? localStorage : sessionStorage;
  if (keep) localStorage.setItem("remember", "1");
  store.setItem("access_token", access);
  store.setItem("refresh_token", refresh);
}

export function clearTokens() {
  for (const s of [localStorage, sessionStorage])
    for (const k of ["access_token", "refresh_token", "remember"]) s.removeItem(k);
}

export function logout() {
  clearTokens();
  window.location.href = "/login";
}

let refreshing: Promise<boolean> | null = null;

async function tryRefresh(): Promise<boolean> {
  refreshing ??= (async () => {
    const rt = getToken("refresh_token");
    if (!rt) return false;
    try {
      const res = await fetch(`${API}/auth/refresh`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: rt }),
      });
      if (!res.ok) return false;
      const b = await res.json();
      setTokens(b.access_token, b.refresh_token);
      return true;
    } catch { return false; }
  })();
  const ok = await refreshing;
  refreshing = null;
  return ok;
}

export async function api(path: string, opts: RequestInit = {}, retried = false): Promise<any> {
  const token = getToken();
  const res = await fetch(`${API}${path}`, {
    ...opts,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(opts.headers ?? {}),
    },
  });
  if (res.status === 401 && typeof window !== "undefined" && !path.startsWith("/auth")) {
    // access token expired → try one silent refresh, else back to login
    if (!retried && (await tryRefresh())) return api(path, opts, true);
    logout();
    throw new Error("Session expired");
  }
  if (!res.ok) {
    const b = await res.json().catch(() => ({}));
    throw new Error(b?.detail ?? `HTTP ${res.status}`);
  }
  return res.status === 204 ? null : res.json();
}

export function roleFromToken(): string | null {
  const t = getToken();
  if (!t) return null;
  try { return JSON.parse(atob(t.split(".")[1])).role ?? null; } catch { return null; }
}
