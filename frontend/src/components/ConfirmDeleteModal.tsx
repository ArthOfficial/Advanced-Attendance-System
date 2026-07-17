"use client";
import { useState } from "react";

export default function ConfirmDeleteModal({ title, children, requireText, busy, onConfirm, onCancel }: {
  title: string;
  children?: React.ReactNode;
  requireText?: string;      // user must type this exactly to enable the button
  busy?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  const [typed, setTyped] = useState("");
  const blocked = !!requireText && typed !== requireText;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4" onClick={onCancel}>
      <div className="w-full max-w-md space-y-4 rounded-2xl border border-zinc-700 bg-zinc-900 p-6 shadow-2xl"
           onClick={e => e.stopPropagation()}>
        <h2 className="text-lg font-semibold text-red-400">🗑️ {title}</h2>
        <div className="max-h-72 space-y-2 overflow-y-auto text-sm text-zinc-300">{children}</div>
        {requireText && (
          <div className="space-y-1">
            <p className="text-sm text-zinc-400">Type <code className="rounded bg-zinc-800 px-1 font-mono text-red-300">{requireText}</code> to confirm:</p>
            <input className="w-full rounded-lg border border-zinc-700 bg-zinc-800 p-2 text-sm outline-none focus:border-red-500"
                   value={typed} onChange={e => setTyped(e.target.value)} autoFocus />
          </div>
        )}
        <div className="flex justify-end gap-2">
          <button className="rounded-lg bg-zinc-800 px-4 py-2 text-sm hover:bg-zinc-700" onClick={onCancel}>Cancel</button>
          <button className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium hover:bg-red-500 disabled:opacity-40"
                  disabled={blocked || busy} onClick={onConfirm}>
            {busy ? "Deleting…" : "Confirm delete"}
          </button>
        </div>
      </div>
    </div>
  );
}

export function Collapse({ label, items }: { label: string; items: string[] }) {
  return (
    <details className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
      <summary className="cursor-pointer select-none text-zinc-200">
        {label} <span className="text-zinc-500">({items.length})</span>
      </summary>
      <ul className="mt-2 list-inside list-disc space-y-1 text-zinc-400">
        {items.length ? items.map((i, k) => <li key={k}>{i}</li>) : <li className="list-none text-zinc-600">None</li>}
      </ul>
    </details>
  );
}
