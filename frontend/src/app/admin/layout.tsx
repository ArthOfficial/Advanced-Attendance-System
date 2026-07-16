"use client";
import { useEffect, useState } from "react";
import { roleFromToken } from "@/lib/api";

const NAV = [
  ["/admin", "📊 Dashboard"],
  ["/admin/academic", "🏛️ Faculties & Departments"],
  ["/admin/teachers", "👥 Teachers"],
  ["/admin/kiosks", "🖥️ Kiosks"],
  ["/admin/audit", "📜 Audit log"],
  ["/admin/network", "🌐 Network"],
] as const;

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const [ok, setOk] = useState(false);
  useEffect(() => {
    if (roleFromToken() !== "admin") { window.location.href = "/login"; return; }
    setOk(true);
  }, []);
  if (!ok) return null;
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 md:flex">
      <aside className="md:w-56 shrink-0 border-b md:border-b-0 md:border-r border-zinc-800 p-4 space-y-1">
        <div className="mb-4 font-semibold">SmartCampus Admin</div>
        {NAV.map(([href, label]) => (
          <a key={href} href={href} className="block rounded-lg px-3 py-2 text-sm hover:bg-zinc-800">{label}</a>
        ))}
        <button className="mt-4 px-3 text-sm text-zinc-500 hover:text-zinc-300"
                onClick={() => { localStorage.clear(); window.location.href = "/login"; }}>
          Sign out
        </button>
      </aside>
      <main className="flex-1 p-6">{children}</main>
    </div>
  );
}
