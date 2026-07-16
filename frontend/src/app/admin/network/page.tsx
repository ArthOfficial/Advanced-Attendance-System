"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

const input = "rounded-lg bg-zinc-900 border border-zinc-800 px-3 py-2 text-sm";
const btn = "rounded-lg bg-indigo-600 px-3 py-2 text-sm hover:bg-indigo-500";

export default function Network() {
  const [enabled, setEnabled] = useState(false);
  const [cidrs, setCidrs] = useState<string[]>([]);
  const [add, setAdd] = useState("");
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  useEffect(() => {
    api("/admin/settings/network").then(v => { setEnabled(v.enabled); setCidrs(v.cidrs); }).catch(e => setErr(e.message));
  }, []);

  const save = (en: boolean, cs: string[]) =>
    api("/admin/settings/network", { method: "PUT", body: JSON.stringify({ enabled: en, cidrs: cs }) })
      .then(v => { setEnabled(v.enabled); setCidrs(v.cidrs); setMsg("Saved."); setErr(""); })
      .catch(e => { setErr(e.message); setMsg(""); });

  return (
    <div className="space-y-6 max-w-xl">
      <h1 className="text-2xl font-semibold">Network validation</h1>
      <p className="text-sm text-zinc-400">
        When enabled, teachers can only scan attendance QR codes from the allowed networks below.
        Loopback (localhost) is always allowed for testing.
      </p>
      {err && <p className="text-red-400">{err}</p>}
      {msg && <p className="text-green-400">{msg}</p>}

      <label className="flex items-center gap-3">
        <input type="checkbox" className="h-5 w-5 accent-indigo-600" checked={enabled}
               onChange={e => save(e.target.checked, cidrs)} />
        <span>Restrict scanning to allowed networks</span>
      </label>

      <div className="space-y-2">
        <div className="flex gap-2">
          <input className={input} placeholder="CIDR e.g. 192.168.0.0/16" value={add} onChange={e => setAdd(e.target.value)} />
          <button className={btn} onClick={() => { if (add) { save(enabled, [...cidrs, add.trim()]); setAdd(""); } }}>Add</button>
        </div>
        <ul className="divide-y divide-zinc-800 rounded-xl bg-zinc-900">
          {cidrs.map(c => (
            <li key={c} className="flex items-center justify-between px-4 py-2">
              <code className="font-mono text-sm">{c}</code>
              <button className="text-sm text-red-400 hover:text-red-300"
                      onClick={() => save(enabled, cidrs.filter(x => x !== c))}>Remove</button>
            </li>
          ))}
          {!cidrs.length && <li className="px-4 py-3 text-sm text-zinc-500">No networks added.</li>}
        </ul>
      </div>
    </div>
  );
}
