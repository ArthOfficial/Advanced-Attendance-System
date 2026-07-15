"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { API, roleFromToken } from "@/lib/api";

export default function Login() {
  const [identifier, setId] = useState("");
  const [password, setPw] = useState("");
  const [err, setErr] = useState("");
  const router = useRouter();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr("");
    const res = await fetch(`${API}/auth/login`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ identifier, password }),
    });
    if (!res.ok) { setErr("Invalid credentials"); return; }
    const b = await res.json();
    localStorage.setItem("access_token", b.access_token);
    localStorage.setItem("refresh_token", b.refresh_token);
    if (b.force_password_reset) { router.push("/change-password"); return; }
    const role = roleFromToken();
    router.push(role === "kiosk" ? "/kiosk" : role === "teacher" ? "/scan" : "/");
  }

  return (
    <main className="min-h-screen flex items-center justify-center bg-zinc-950 text-zinc-100">
      <form onSubmit={submit} className="w-80 space-y-4 rounded-2xl bg-zinc-900 p-8 shadow-xl">
        <h1 className="text-xl font-semibold">SmartCampus</h1>
        <input className="w-full rounded-lg bg-zinc-800 p-3 text-sm" placeholder="Employee ID or email"
               value={identifier} onChange={e => setId(e.target.value)} />
        <input className="w-full rounded-lg bg-zinc-800 p-3 text-sm" type="password" placeholder="Password"
               value={password} onChange={e => setPw(e.target.value)} />
        {err && <p className="text-sm text-red-400">{err}</p>}
        <button className="w-full rounded-lg bg-emerald-600 p-3 text-sm font-medium hover:bg-emerald-500">
          Sign in
        </button>
      </form>
    </main>
  );
}
