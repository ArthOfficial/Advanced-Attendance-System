"use client";
import { useEffect, useState } from "react";
import { API, roleFromToken } from "@/lib/api";

export default function Home() {
  const [role, setRole] = useState<string | null>(null);

  useEffect(() => {
    const r = roleFromToken();
    if (!r) { window.location.href = "/login"; return; }
    setRole(r);
  }, []);

  if (!role) return null;
  const link = "block rounded-xl bg-zinc-900 p-5 hover:bg-zinc-800";
  return (
    <main className="min-h-screen flex items-center justify-center bg-zinc-950 text-zinc-100">
      <div className="w-96 space-y-3">
        <h1 className="mb-4 text-2xl font-semibold">SmartCampus</h1>
        {role === "teacher" && <>
          <a className={link} href="/scan">📷 Scan attendance QR</a>
          <a className={link} href="/me">👤 My attendance</a>
        </>}
        {role === "kiosk" && <a className={link} href="/kiosk">🖥️ Open kiosk display</a>}
        {role === "admin" && <a className={link} href={`${API}/docs`}>⚙️ Admin API console (/docs)</a>}
        <button className="text-sm text-zinc-500 hover:text-zinc-300"
                onClick={() => { localStorage.clear(); window.location.href = "/login"; }}>
          Sign out
        </button>
      </div>
    </main>
  );
}
