"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type Profile = { full_name: string; employee_id: string; faculty_name: string;
                 department_name: string; designation: string | null };
type Hist = { records: { date: string; status: string; method: string; marked_at: string | null }[];
              present_days: number; total_sessions: number };

export default function Me() {
  const [p, setP] = useState<Profile | null>(null);
  const [h, setH] = useState<Hist | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    Promise.all([api("/me"), api("/attendance/me")])
      .then(([prof, hist]) => { setP(prof); setH(hist); })
      .catch(e => setErr((e as Error).message));
  }, []);

  if (err) return <main className="min-h-screen bg-zinc-950 p-8 text-red-400">{err}</main>;
  if (!p || !h) return null;

  return (
    <main className="min-h-screen bg-zinc-950 p-6 text-zinc-100">
      <div className="mx-auto max-w-2xl space-y-6">
        <div className="rounded-2xl bg-zinc-900 p-6">
          <h1 className="text-xl font-semibold">{p.full_name}</h1>
          <p className="text-sm text-zinc-400">{p.employee_id} · {p.designation ?? "Teacher"}</p>
          <p className="text-sm text-zinc-400">{p.faculty_name} → {p.department_name}</p>
        </div>
        <div className="flex gap-4">
          <div className="flex-1 rounded-2xl bg-zinc-900 p-6 text-center">
            <p className="text-3xl font-bold text-emerald-400">{h.present_days}</p>
            <p className="text-sm text-zinc-400">Days present</p>
          </div>
          <div className="flex-1 rounded-2xl bg-zinc-900 p-6 text-center">
            <p className="text-3xl font-bold">{h.total_sessions}</p>
            <p className="text-sm text-zinc-400">Total sessions</p>
          </div>
        </div>
        <table className="w-full rounded-2xl bg-zinc-900 text-sm">
          <thead><tr className="text-left text-zinc-400">
            <th className="p-3">Date</th><th>Status</th><th>Method</th><th>Time</th>
          </tr></thead>
          <tbody>
            {h.records.map(r => (
              <tr key={r.date} className="border-t border-zinc-800">
                <td className="p-3">{r.date}</td>
                <td className={r.status === "present" ? "text-emerald-400" : "text-red-400"}>{r.status}</td>
                <td>{r.method}</td>
                <td>{r.marked_at ? new Date(r.marked_at).toLocaleTimeString() : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <a className="text-sm text-zinc-500 hover:text-zinc-300" href="/">← Home</a>
      </div>
    </main>
  );
}
