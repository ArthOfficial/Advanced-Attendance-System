"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type Kiosk = { id: string; name: string; location: string | null; is_active: boolean };
type Created = Kiosk & { username: string; password: string };

const input = "rounded-lg bg-zinc-900 border border-zinc-800 px-3 py-2 text-sm";
const btn = "rounded-lg bg-indigo-600 px-3 py-2 text-sm hover:bg-indigo-500 disabled:opacity-50";

export default function Kiosks() {
  const [kiosks, setKiosks] = useState<Kiosk[]>([]);
  const [name, setName] = useState("");
  const [location, setLocation] = useState("");
  const [created, setCreated] = useState<Created | null>(null);
  const [err, setErr] = useState("");

  const load = () => api("/kiosks").then(setKiosks).catch(e => setErr(e.message));
  useEffect(() => { load(); }, []);

  const create = () => {
    api("/kiosks", { method: "POST", body: JSON.stringify({ name, location: location || null }) })
      .then(k => { setCreated(k); setName(""); setLocation(""); setErr(""); load(); })
      .catch(e => setErr(e.message));
  };

  const toggle = (k: Kiosk) =>
    api(`/kiosks/${k.id}`, { method: "PATCH", body: JSON.stringify({ is_active: !k.is_active }) })
      .then(load).catch(e => setErr(e.message));

  return (
    <div className="space-y-6 max-w-3xl">
      <h1 className="text-2xl font-semibold">Kiosks</h1>
      {err && <p className="text-red-400">{err}</p>}

      <div className="flex flex-wrap gap-2">
        <input className={input} placeholder="Kiosk name *" value={name} onChange={e => setName(e.target.value)} />
        <input className={input} placeholder="Location" value={location} onChange={e => setLocation(e.target.value)} />
        <button className={btn} disabled={!name} onClick={create}>Create kiosk</button>
      </div>

      {created && (
        <div className="rounded-xl border border-yellow-600 bg-yellow-950/40 p-4 text-sm">
          <p className="mb-2 font-medium text-yellow-300">⚠️ Save these credentials now — the password is shown only once.</p>
          <p>Username: <code className="font-mono">{created.username}</code></p>
          <p>Password: <code className="font-mono">{created.password}</code></p>
          <button className="mt-2 text-yellow-400 hover:text-yellow-200" onClick={() => setCreated(null)}>Dismiss</button>
        </div>
      )}

      <ul className="divide-y divide-zinc-800 rounded-xl bg-zinc-900">
        {kiosks.map(k => (
          <li key={k.id} className="flex items-center justify-between px-4 py-3">
            <span>
              {k.name} {k.location && <span className="text-sm text-zinc-500">— {k.location}</span>}
              <span className={`ml-2 rounded px-2 py-0.5 text-xs ${k.is_active ? "bg-green-900 text-green-300" : "bg-zinc-800 text-zinc-400"}`}>
                {k.is_active ? "active" : "disabled"}
              </span>
            </span>
            <button className="text-sm text-zinc-400 hover:text-white" onClick={() => toggle(k)}>
              {k.is_active ? "Disable" : "Enable"}
            </button>
          </li>
        ))}
        {!kiosks.length && <li className="px-4 py-3 text-sm text-zinc-500">No kiosks yet.</li>}
      </ul>
    </div>
  );
}
