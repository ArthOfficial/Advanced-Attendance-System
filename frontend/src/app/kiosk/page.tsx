"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import QRCode from "qrcode";
import { api } from "@/lib/api";

export default function Kiosk() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [code, setCode] = useState("");
  const [left, setLeft] = useState(30);

  const refresh = useCallback(async () => {
    try {
      const b = await api("/kiosk/qr");
      setCode(b.session_code);
      setLeft(b.ttl);
      if (canvasRef.current)
        QRCode.toCanvas(canvasRef.current, JSON.stringify({ payload: b.payload, sig: b.sig }),
                        { width: 420, margin: 1 });
    } catch { window.location.href = "/login"; }
  }, []);

  useEffect(() => {
    refresh();
    const qr = setInterval(refresh, 30_000);
    const tick = setInterval(() => setLeft(l => Math.max(0, l - 1)), 1_000);
    return () => { clearInterval(qr); clearInterval(tick); };
  }, [refresh]);

  return (
    <main className="min-h-screen flex flex-col items-center justify-center gap-6 bg-zinc-950 text-zinc-100">
      <h1 className="text-2xl font-semibold">Scan to mark attendance</h1>
      <canvas ref={canvasRef} className="rounded-xl bg-white p-2" />
      <div className="h-1 w-[420px] overflow-hidden rounded bg-zinc-800">
        <div className="h-full bg-emerald-500 transition-all" style={{ width: `${(left / 30) * 100}%` }} />
      </div>
      <p className="text-sm text-zinc-400">{code} · refreshes every 30s</p>
    </main>
  );
}
