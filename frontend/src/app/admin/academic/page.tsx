"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import ConfirmDeleteModal, { Collapse } from "@/components/ConfirmDeleteModal";

type Fac = { id: string; name: string };
type Dep = { id: string; name: string; faculty_id: string };
type Kid = { id: string; name?: string; employee_id?: string; full_name?: string };
type Pending = { kind: "faculty" | "department"; id: string; name: string;
  departments: Kid[]; teachers: Kid[]; faculty?: Kid | null };

const input = "rounded-lg bg-zinc-900 border border-zinc-800 px-3 py-2 text-sm";
const btn = "rounded-lg bg-indigo-600 px-3 py-2 text-sm hover:bg-indigo-500";

export default function Academic() {
  const [faculties, setFaculties] = useState<Fac[]>([]);
  const [departments, setDepartments] = useState<Dep[]>([]);
  const [fName, setFName] = useState("");
  const [dName, setDName] = useState("");
  const [dFac, setDFac] = useState("");
  const [err, setErr] = useState("");
  const [pending, setPending] = useState<Pending | null>(null);
  const [busy, setBusy] = useState(false);

  const load = () => {
    api("/faculties").then(setFaculties).catch(e => setErr(e.message));
    api("/departments").then(setDepartments).catch(() => {});
  };
  useEffect(load, []);

  const run = (p: Promise<unknown>) => p.then(() => { setErr(""); load(); }).catch(e => setErr(e.message));

  const askDeleteFaculty = async (f: Fac) => {
    try {
      const kids = await api(`/faculties/${f.id}/children`);
      setPending({ kind: "faculty", id: f.id, name: f.name,
                   departments: kids.departments, teachers: kids.teachers });
    } catch (e) { setErr((e as Error).message); }
  };

  const askDeleteDepartment = async (d: Dep) => {
    try {
      const kids = await api(`/departments/${d.id}/children`);
      setPending({ kind: "department", id: d.id, name: d.name,
                   departments: [], teachers: kids.teachers, faculty: kids.faculty });
    } catch (e) { setErr((e as Error).message); }
  };

  const confirmDelete = async () => {
    if (!pending) return;
    setBusy(true);
    const path = pending.kind === "faculty" ? "faculties" : "departments";
    try {
      await api(`/${path}/${pending.id}?force=true`, { method: "DELETE" });
      setPending(null); setErr(""); load();
    } catch (e) { setErr((e as Error).message); } finally { setBusy(false); }
  };

  return (
    <div className="space-y-8 max-w-3xl">
      <h1 className="text-2xl font-semibold">Faculties & Departments</h1>
      {err && <p className="text-red-400">{err}</p>}

      <section className="space-y-3">
        <h2 className="text-lg font-medium">Faculties</h2>
        <div className="flex gap-2">
          <input className={input} placeholder="Faculty name" value={fName} onChange={e => setFName(e.target.value)} />
          <button className={btn} onClick={() => { if (fName) run(api("/faculties", { method: "POST", body: JSON.stringify({ name: fName }) })); setFName(""); }}>Add</button>
        </div>
        <ul className="divide-y divide-zinc-800 rounded-xl bg-zinc-900">
          {faculties.map(f => (
            <li key={f.id} className="flex items-center justify-between px-4 py-2">
              <span>{f.name}</span>
              <span className="space-x-3 text-sm">
                <button className="text-zinc-400 hover:text-white" onClick={() => {
                  const n = prompt("New name", f.name);
                  if (n) run(api(`/faculties/${f.id}`, { method: "PATCH", body: JSON.stringify({ name: n }) }));
                }}>Rename</button>
                <button className="text-red-400 hover:text-red-300" onClick={() => askDeleteFaculty(f)}>Delete</button>
              </span>
            </li>
          ))}
          {!faculties.length && <li className="px-4 py-3 text-sm text-zinc-500">No faculties yet.</li>}
        </ul>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-medium">Departments</h2>
        <div className="flex flex-wrap gap-2">
          <input className={input} placeholder="Department name" value={dName} onChange={e => setDName(e.target.value)} />
          <select className={input} value={dFac} onChange={e => setDFac(e.target.value)}>
            <option value="">Select faculty…</option>
            {faculties.map(f => <option key={f.id} value={f.id}>{f.name}</option>)}
          </select>
          <button className={btn} onClick={() => { if (dName && dFac) run(api("/departments", { method: "POST", body: JSON.stringify({ name: dName, faculty_id: dFac }) })); setDName(""); }}>Add</button>
        </div>
        <ul className="divide-y divide-zinc-800 rounded-xl bg-zinc-900">
          {departments.map(d => (
            <li key={d.id} className="flex items-center justify-between px-4 py-2">
              <span>{d.name} <span className="text-sm text-zinc-500">— {faculties.find(f => f.id === d.faculty_id)?.name ?? "?"}</span></span>
              <span className="space-x-3 text-sm">
                <button className="text-zinc-400 hover:text-white" onClick={() => {
                  const n = prompt("New name", d.name);
                  if (n) run(api(`/departments/${d.id}`, { method: "PATCH", body: JSON.stringify({ name: n }) }));
                }}>Rename</button>
                <button className="text-red-400 hover:text-red-300" onClick={() => askDeleteDepartment(d)}>Delete</button>
              </span>
            </li>
          ))}
          {!departments.length && <li className="px-4 py-3 text-sm text-zinc-500">No departments yet.</li>}
        </ul>
      </section>

      {pending && (
        <ConfirmDeleteModal
          title={`Delete ${pending.kind} "${pending.name}"?`}
          busy={busy} onConfirm={confirmDelete} onCancel={() => setPending(null)}>
          <p>This will permanently delete everything below. Teachers lose their accounts and attendance history.</p>
          {pending.kind === "faculty" && (
            <Collapse label="🏛️ Departments to be deleted" items={pending.departments.map(d => d.name!)} />
          )}
          {pending.kind === "department" && pending.faculty && (
            <p className="text-zinc-500">Parent faculty <b className="text-zinc-300">{pending.faculty.name}</b> is NOT deleted.</p>
          )}
          <Collapse label="👥 Teachers to be deleted"
                    items={pending.teachers.map(t => `${t.employee_id} — ${t.full_name}`)} />
        </ConfirmDeleteModal>
      )}
    </div>
  );
}
