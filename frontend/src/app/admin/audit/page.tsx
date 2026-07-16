"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type Row = { id: string; action: string; entity: string | null; detail: unknown;
  ip: string | null; actor: string | null; at: string };

const input = "rounded-lg bg-zinc-900 border border-zinc-800 px-3 py-2 text-sm";

export default function Audit() {
  const [rows, setRows] = useState<Row[]>([]);
  const [q, setQ] = useState("");
  const [action, setAction] = useState("");
  const [offset, setOffset] = useState(0);
  const [err, setErr] = useState("");
  const limit = 50;

  useEffect(() => {
    const p = new URLSearchParams({ limit: String(limit), offset: String(offset) });
    if (q) p.set("q", q);
    if (action) p.set("action", action);
    const t = setTimeout(() =>
      api(`/admin/audit?${p}`).then(r => { setRows(r); setErr(""); }).catch(e => setErr(e.message)), 300);
    return () => clearTimeout(t);
  }, [q, action, offset]);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Audit log</h1>
      <div className="flex gap-2">
        <input className={input} placeholder="Search detail…" value={q} onChange={e => { setQ(e.target.value); setOffset(0); }} />
        <input className={input} placeholder="Action filter (e.g. login, scan)" value={action} onChange={e => { setAction(e.target.value); setOffset(0); }} />
      </div>
      {err && <p className="text-red-400">{err}</p>}
      <div className="overflow-x-auto rounded-xl bg-zinc-900">
        <table className="w-full text-sm">
          <thead><tr className="text-left text-zinc-400">
            <th className="px-4 py-2">Time</th><th className="px-4 py-2">Action</th>
            <th className="px-4 py-2">Entity</th><th className="px-4 py-2">Detail</th><th className="px-4 py-2">Actor</th>
          </tr></thead>
          <tbody className="divide-y divide-zinc-800">
            {rows.map(r => (
              <tr key={r.id}>
                <td className="whitespace-nowrap px-4 py-2 text-zinc-400">{r.at.replace("T", " ").slice(0, 19)}</td>
                <td className="px-4 py-2 font-mono text-xs">{r.action}</td>
                <td className="px-4 py-2 font-mono text-xs">{r.entity ?? "—"}</td>
                <td className="max-w-md truncate px-4 py-2 text-xs text-zinc-400">{r.detail ? JSON.stringify(r.detail) : "—"}</td>
                <td className="px-4 py-2 font-mono text-xs">{r.actor?.slice(0, 8) ?? "—"}</td>
              </tr>
            ))}
            {!rows.length && <tr><td className="px-4 py-3 text-zinc-500" colSpan={5}>No entries.</td></tr>}
          </tbody>
        </table>
      </div>
      <div className="flex gap-2 text-sm">
        <button className="rounded-lg bg-zinc-800 px-3 py-1 disabled:opacity-40" disabled={offset === 0}
                onClick={() => setOffset(Math.max(0, offset - limit))}>← Newer</button>
        <button className="rounded-lg bg-zinc-800 px-3 py-1 disabled:opacity-40" disabled={rows.length < limit}
                onClick={() => setOffset(offset + limit)}>Older →</button>
      </div>
    </div>
  );
}
