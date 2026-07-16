"use client";
import { useEffect, useState } from "react";
import { API, api, getToken } from "@/lib/api";

type Opt = { id: string; name: string; faculty_id?: string };
type Teacher = { id: string; employee_id: string; full_name: string; dob: string;
  faculty_id: string; department_id: string; designation: string | null; email: string | null };
type Preview = { import_id: string; valid: Record<string, unknown>[];
  duplicates: { row: Record<string, unknown>; existing: Record<string, unknown> }[];
  rejected: { row: Record<string, unknown>; reason: string }[];
  counts: { valid: number; duplicates: number; rejected: number } };

const input = "rounded-lg bg-zinc-900 border border-zinc-800 px-3 py-2 text-sm";
const btn = "rounded-lg bg-indigo-600 px-3 py-2 text-sm hover:bg-indigo-500 disabled:opacity-50";

export default function Teachers() {
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [faculties, setFaculties] = useState<Opt[]>([]);
  const [departments, setDepartments] = useState<Opt[]>([]);
  const [form, setForm] = useState({ employee_id: "", full_name: "", dob: "", faculty_id: "", department_id: "", designation: "", email: "" });
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");
  const [preview, setPreview] = useState<Preview | null>(null);
  const [busy, setBusy] = useState(false);

  const load = () => {
    api("/teachers").then(setTeachers).catch(e => setErr(e.message));
    api("/faculties").then(setFaculties).catch(() => {});
    api("/departments").then(setDepartments).catch(() => {});
  };
  useEffect(load, []);

  const set = (k: string, v: string) => setForm(f => ({ ...f, [k]: v }));

  const create = () => {
    setErr(""); setMsg("");
    api("/teachers", { method: "POST", body: JSON.stringify({
      ...form, designation: form.designation || null, email: form.email || null,
    }) }).then(() => {
      setMsg(`Created. Default password = DOB as DDMMYYYY (teacher must change it on first login).`);
      setForm({ employee_id: "", full_name: "", dob: "", faculty_id: "", department_id: "", designation: "", email: "" });
      load();
    }).catch(e => setErr(e.message));
  };

  const upload = async (file: File) => {
    setErr(""); setMsg(""); setBusy(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await fetch(`${API}/teachers/import/preview`, {
        method: "POST", body: fd,
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      const b = await res.json();
      if (!res.ok) throw new Error(b?.detail ?? `HTTP ${res.status}`);
      setPreview(b);
    } catch (e) { setErr((e as Error).message); } finally { setBusy(false); }
  };

  const commit = (action: "skip" | "override") => {
    if (!preview) return;
    setBusy(true);
    api("/teachers/import/commit", { method: "POST", body: JSON.stringify({ import_id: preview.import_id, duplicate_action: action }) })
      .then(r => { setMsg(`Import done: ${r.created} created, ${r.updated} updated, ${r.skipped} skipped, ${r.rejected} rejected.`); setPreview(null); load(); })
      .catch(e => setErr(e.message)).finally(() => setBusy(false));
  };

  const facName = (id: string) => faculties.find(f => f.id === id)?.name ?? "?";
  const depName = (id: string) => departments.find(d => d.id === id)?.name ?? "?";

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-semibold">Teachers</h1>
      {err && <p className="text-red-400">{err}</p>}
      {msg && <p className="text-green-400">{msg}</p>}

      <section className="space-y-3 max-w-3xl">
        <h2 className="text-lg font-medium">Add teacher</h2>
        <div className="grid gap-2 md:grid-cols-3">
          <input className={input} placeholder="Employee ID *" value={form.employee_id} onChange={e => set("employee_id", e.target.value)} />
          <input className={input} placeholder="Full name *" value={form.full_name} onChange={e => set("full_name", e.target.value)} />
          <input className={input} type="date" title="Date of birth" value={form.dob} onChange={e => set("dob", e.target.value)} />
          <select className={input} value={form.faculty_id} onChange={e => { set("faculty_id", e.target.value); set("department_id", ""); }}>
            <option value="">Faculty *</option>
            {faculties.map(f => <option key={f.id} value={f.id}>{f.name}</option>)}
          </select>
          <select className={input} value={form.department_id} onChange={e => set("department_id", e.target.value)} disabled={!form.faculty_id}>
            <option value="">Department *</option>
            {departments.filter(d => d.faculty_id === form.faculty_id).map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
          <input className={input} placeholder="Designation" value={form.designation} onChange={e => set("designation", e.target.value)} />
          <input className={input} placeholder="Email (optional)" value={form.email} onChange={e => set("email", e.target.value)} />
        </div>
        <button className={btn} disabled={!form.employee_id || !form.full_name || !form.dob || !form.department_id} onClick={create}>Create teacher</button>
      </section>

      <section className="space-y-3 max-w-3xl">
        <h2 className="text-lg font-medium">Import from file (CSV / XLSX)</h2>
        <input type="file" accept=".csv,.xlsx" disabled={busy}
               className="text-sm file:mr-3 file:rounded-lg file:border-0 file:bg-zinc-800 file:px-3 file:py-2 file:text-zinc-100"
               onChange={e => e.target.files?.[0] && upload(e.target.files[0])} />
        {preview && (
          <div className="space-y-3 rounded-xl bg-zinc-900 p-4">
            <p className="text-sm">Preview: <span className="text-green-400">{preview.counts.valid} valid</span> · <span className="text-yellow-400">{preview.counts.duplicates} duplicates</span> · <span className="text-red-400">{preview.counts.rejected} rejected</span></p>
            {preview.duplicates.length > 0 && (
              <div className="max-h-48 overflow-auto text-xs">
                <p className="mb-1 text-yellow-400">Duplicates (existing → incoming):</p>
                {preview.duplicates.map((d, i) => (
                  <p key={i} className="text-zinc-400">{String(d.existing.employee_id)}: {String(d.existing.full_name)} → {String(d.row.full_name)}</p>
                ))}
              </div>
            )}
            {preview.rejected.length > 0 && (
              <div className="max-h-48 overflow-auto text-xs">
                <p className="mb-1 text-red-400">Rejected:</p>
                {preview.rejected.map((r, i) => <p key={i} className="text-zinc-400">{String(r.row.employee_id ?? "?")}: {r.reason}</p>)}
              </div>
            )}
            <div className="flex gap-2">
              <button className={btn} disabled={busy} onClick={() => commit("skip")}>Commit (skip duplicates)</button>
              <button className={btn} disabled={busy} onClick={() => commit("override")}>Commit (override duplicates)</button>
              <button className="rounded-lg bg-zinc-800 px-3 py-2 text-sm hover:bg-zinc-700" onClick={() => setPreview(null)}>Cancel</button>
            </div>
          </div>
        )}
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-medium">All teachers ({teachers.length})</h2>
        <div className="overflow-x-auto rounded-xl bg-zinc-900">
          <table className="w-full text-sm">
            <thead><tr className="text-left text-zinc-400">
              <th className="px-4 py-2">Employee ID</th><th className="px-4 py-2">Name</th>
              <th className="px-4 py-2">Faculty</th><th className="px-4 py-2">Department</th>
              <th className="px-4 py-2">Designation</th><th className="px-4 py-2">Email</th>
            </tr></thead>
            <tbody className="divide-y divide-zinc-800">
              {teachers.map(t => (
                <tr key={t.id}>
                  <td className="px-4 py-2 font-mono">{t.employee_id}</td>
                  <td className="px-4 py-2">{t.full_name}</td>
                  <td className="px-4 py-2">{facName(t.faculty_id)}</td>
                  <td className="px-4 py-2">{depName(t.department_id)}</td>
                  <td className="px-4 py-2">{t.designation ?? "—"}</td>
                  <td className="px-4 py-2">{t.email ?? "—"}</td>
                </tr>
              ))}
              {!teachers.length && <tr><td className="px-4 py-3 text-zinc-500" colSpan={6}>No teachers yet.</td></tr>}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
