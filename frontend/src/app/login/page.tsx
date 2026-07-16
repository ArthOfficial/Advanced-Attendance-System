"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { API, roleFromToken, setTokens } from "@/lib/api";

export default function Login() {
  const [identifier, setId] = useState("");
  const [password, setPw] = useState("");
  const [remember, setRemember] = useState(false);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const router = useRouter();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr(""); setBusy(true);
    try {
      const res = await fetch(`${API}/auth/login`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ identifier: identifier.trim(), password }),
      });
      if (!res.ok) {
        const b = await res.json().catch(() => ({}));
        setErr(b?.detail ?? "Invalid credentials"); return;
      }
      const b = await res.json();
      setTokens(b.access_token, b.refresh_token, remember);
      if (b.force_password_reset) { router.push("/change-password"); return; }
      const role = roleFromToken();
      router.push(role === "kiosk" ? "/kiosk" : role === "teacher" ? "/me" : "/admin");
    } catch {
      setErr("Cannot reach the server. Is the backend running?");
    } finally { setBusy(false); }
  }

  const input = "w-full rounded-lg border border-zinc-700 bg-zinc-800 p-3 text-sm outline-none focus:border-emerald-500";
  return (
    <main className="min-h-screen flex items-center justify-center bg-zinc-950 text-zinc-100 p-4">
      <form onSubmit={submit} className="w-full max-w-sm space-y-4 rounded-2xl border border-zinc-800 bg-zinc-900 p-8 shadow-xl">
        <div className="text-center">
          <div className="text-4xl">🎓</div>
          <h1 className="mt-2 text-2xl font-semibold">SmartCampus</h1>
          <p className="text-sm text-zinc-400">University Attendance</p>
        </div>
        <div className="space-y-1">
          <label className="text-xs text-zinc-400" htmlFor="id">Employee ID or email</label>
          <input id="id" className={input} placeholder="e.g. T001" autoFocus autoComplete="username"
                 value={identifier} onChange={e => setId(e.target.value)} />
        </div>
        <div className="space-y-1">
          <label className="text-xs text-zinc-400" htmlFor="pw">Password</label>
          <input id="pw" className={input} type="password" placeholder="••••••••" autoComplete="current-password"
                 value={password} onChange={e => setPw(e.target.value)} />
        </div>
        {err && <p className="rounded-lg bg-red-950/60 px-3 py-2 text-sm text-red-400">{err}</p>}
        <label className="flex items-center gap-2 text-sm text-zinc-300">
          <input type="checkbox" className="h-4 w-4 accent-emerald-600" checked={remember}
                 onChange={e => setRemember(e.target.checked)} />
          Keep me logged in
        </label>
        <button disabled={busy || !identifier || !password}
                className="w-full rounded-lg bg-emerald-600 p-3 text-sm font-medium hover:bg-emerald-500 disabled:opacity-50">
          {busy ? "Signing in…" : "Sign in"}
        </button>
        <p className="text-center text-xs text-zinc-500">Teachers: first password is your date of birth (DDMMYYYY)</p>
      </form>
    </main>
  );
}
