"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, roleFromToken } from "@/lib/api";

export default function ChangePassword() {
  const [oldPw, setOld] = useState("");
  const [newPw, setNew] = useState("");
  const [err, setErr] = useState("");
  const router = useRouter();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr("");
    try {
      await api("/auth/change-password", {
        method: "POST",
        body: JSON.stringify({ old_password: oldPw, new_password: newPw }),
      });
      const role = roleFromToken();
      router.push(role === "kiosk" ? "/kiosk" : role === "teacher" ? "/scan" : "/");
    } catch (e) { setErr((e as Error).message); }
  }

  return (
    <main className="min-h-screen flex items-center justify-center bg-zinc-950 text-zinc-100">
      <form onSubmit={submit} className="w-80 space-y-4 rounded-2xl bg-zinc-900 p-8 shadow-xl">
        <h1 className="text-xl font-semibold">Set a new password</h1>
        <input className="w-full rounded-lg bg-zinc-800 p-3 text-sm" type="password"
               placeholder="Current password" value={oldPw} onChange={e => setOld(e.target.value)} />
        <input className="w-full rounded-lg bg-zinc-800 p-3 text-sm" type="password"
               placeholder="New password" value={newPw} onChange={e => setNew(e.target.value)} />
        {err && <p className="text-sm text-red-400">{err}</p>}
        <button className="w-full rounded-lg bg-emerald-600 p-3 text-sm font-medium hover:bg-emerald-500">
          Update password
        </button>
      </form>
    </main>
  );
}
