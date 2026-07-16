"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type Stats = { total_teachers: number; present: number; absent: number; percent: number;
  session_code: string | null; session_date: string | null; active_kiosks: number };
type Opt = { id: string; name: string };

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [faculties, setFaculties] = useState<Opt[]>([]);
  const [departments, setDepartments] = useState<Opt[]>([]);
  const [day, setDay] = useState("");
  const [fac, setFac] = useState("");
  const [dep, setDep] = useState("");
  const [err, setErr] = useState("");

  useEffect(() => { api("/faculties").then(setFaculties).catch(() => {}); }, []);
  useEffect(() => {
    setDep("");
    if (fac) api(`/departments?faculty_id=${fac}`).then(setDepartments).catch(() => {});
    else setDepartments([]);
  }, [fac]);
  useEffect(() => {
    const p = new URLSearchParams();
    if (day) p.set("day", day);
    if (fac) p.set("faculty_id", fac);
    if (dep) p.set("department_id", dep);
    api(`/admin/stats?${p}`).then(s => { setStats(s); setErr(""); }).catch(e => setErr(e.message));
  }, [day, fac, dep]);

  const sel = "rounded-lg bg-zinc-900 border border-zinc-800 px-3 py-2 text-sm";
  const tile = "rounded-xl bg-zinc-900 p-5";
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Dashboard</h1>
      <div className="flex flex-wrap gap-3">
        <input type="date" className={sel} value={day} onChange={e => setDay(e.target.value)} />
        <select className={sel} value={fac} onChange={e => setFac(e.target.value)}>
          <option value="">All faculties</option>
          {faculties.map(f => <option key={f.id} value={f.id}>{f.name}</option>)}
        </select>
        <select className={sel} value={dep} onChange={e => setDep(e.target.value)} disabled={!fac}>
          <option value="">All departments</option>
          {departments.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
        </select>
      </div>
      {err && <p className="text-red-400">{err}</p>}
      {stats && (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-5">
          <div className={tile}><div className="text-3xl font-bold">{stats.total_teachers}</div><div className="text-sm text-zinc-400">Teachers</div></div>
          <div className={tile}><div className="text-3xl font-bold text-green-400">{stats.present}</div><div className="text-sm text-zinc-400">Present</div></div>
          <div className={tile}><div className="text-3xl font-bold text-red-400">{stats.absent}</div><div className="text-sm text-zinc-400">Absent</div></div>
          <div className={tile}><div className="text-3xl font-bold">{stats.percent}%</div><div className="text-sm text-zinc-400">Attendance</div></div>
          <div className={tile}><div className="text-3xl font-bold">{stats.active_kiosks}</div><div className="text-sm text-zinc-400">Active kiosks</div></div>
        </div>
      )}
      {stats && <p className="text-sm text-zinc-500">
        Session: {stats.session_code ?? "none"} {stats.session_date && `(${stats.session_date})`}
      </p>}
    </div>
  );
}
