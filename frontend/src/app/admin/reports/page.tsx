"use client";
import { useEffect, useState } from "react";
import { API, api, getToken } from "@/lib/api";

type Row = { name: string | null; employee_id?: string; faculty?: string; department?: string;
  teachers?: number; present: number; total_sessions: number; percent: number };

const input = "rounded-lg bg-zinc-900 border border-zinc-800 px-3 py-2 text-sm";

export default function Reports() {
  const today = new Date().toISOString().slice(0, 10);
  const monthAgo = new Date(Date.now() - 29 * 864e5).toISOString().slice(0, 10);
  const [from, setFrom] = useState(monthAgo);
  const [to, setTo] = useState(today);
  const [groupBy, setGroupBy] = useState("teacher");
  const [rows, setRows] = useState<Row[]>([]);
  const [totalSessions, setTotalSessions] = useState(0);
  const [err, setErr] = useState("");

  const qs = new URLSearchParams({ date_from: from, date_to: to, group_by: groupBy });

  useEffect(() => {
    if (!from || !to) return;
    api(`/admin/reports?${qs}`)
      .then(r => { setRows(r.rows); setTotalSessions(r.total_sessions); setErr(""); })
      .catch(e => setErr(e.message));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [from, to, groupBy]);

  const downloadCsv = async () => {
    const res = await fetch(`${API}/admin/reports?${qs}&fmt=csv`, {
      headers: { Authorization: `Bearer ${getToken()}` } });
    const blob = await res.blob();
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `report-${groupBy}-${from}-${to}.csv`;
    a.click();
  };

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Reports</h1>
      <div className="flex flex-wrap items-center gap-2">
        <input type="date" className={input} value={from} onChange={e => setFrom(e.target.value)} />
        <span className="text-zinc-500">→</span>
        <input type="date" className={input} value={to} onChange={e => setTo(e.target.value)} />
        <select className={input} value={groupBy} onChange={e => setGroupBy(e.target.value)}>
          <option value="teacher">By teacher</option>
          <option value="department">By department</option>
          <option value="faculty">By faculty</option>
        </select>
        <button className="rounded-lg bg-indigo-600 px-3 py-2 text-sm hover:bg-indigo-500" onClick={downloadCsv}>
          ⬇ Download CSV
        </button>
      </div>
      {err && <p className="text-red-400">{err}</p>}
      <p className="text-sm text-zinc-500">{totalSessions} session{totalSessions === 1 ? "" : "s"} in range</p>
      <div className="overflow-x-auto rounded-xl bg-zinc-900">
        <table className="w-full text-sm">
          <thead><tr className="text-left text-zinc-400">
            <th className="px-4 py-2">Name</th>
            {groupBy === "teacher" && <><th className="px-4 py-2">Employee ID</th><th className="px-4 py-2">Faculty</th><th className="px-4 py-2">Department</th></>}
            {groupBy !== "teacher" && <th className="px-4 py-2">Teachers</th>}
            <th className="px-4 py-2">Present</th><th className="px-4 py-2">%</th>
          </tr></thead>
          <tbody className="divide-y divide-zinc-800">
            {rows.map((r, i) => (
              <tr key={i}>
                <td className="px-4 py-2">{r.name ?? "—"}</td>
                {groupBy === "teacher" && <>
                  <td className="px-4 py-2 font-mono text-xs">{r.employee_id}</td>
                  <td className="px-4 py-2">{r.faculty ?? "—"}</td>
                  <td className="px-4 py-2">{r.department ?? "—"}</td>
                </>}
                {groupBy !== "teacher" && <td className="px-4 py-2">{r.teachers}</td>}
                <td className="px-4 py-2 text-green-400">{r.present}</td>
                <td className="px-4 py-2">{r.percent}%</td>
              </tr>
            ))}
            {!rows.length && <tr><td className="px-4 py-3 text-zinc-500" colSpan={6}>No data in range.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
