"use client";
import { useEffect, useRef, useState } from "react";
import jsQR from "jsqr";
import { api } from "@/lib/api";

type Result = { ok: boolean; msg: string } | null;

export default function Scan() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [result, setResult] = useState<Result>(null);
  const [manual, setManual] = useState("");
  const busy = useRef(false);

  async function submit(text: string) {
    if (busy.current) return;
    busy.current = true;
    try {
      const { payload, sig } = JSON.parse(text);
      const r = await api("/attendance/scan", { method: "POST", body: JSON.stringify({ payload, sig }) });
      setResult({ ok: true, msg: `Present ✓ ${r.session_code}` });
    } catch (e) {
      setResult({ ok: false, msg: (e as Error).message });
    }
  }

  useEffect(() => {
    let stream: MediaStream | null = null;
    let raf = 0;
    const canvas = document.createElement("canvas");

    async function start() {
      try {
        stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
        const v = videoRef.current!;
        v.srcObject = stream;
        await v.play();
        // ponytail: BarcodeDetector where present, jsQR frame-scan fallback elsewhere
        const HasBD = "BarcodeDetector" in window;
        const detector = HasBD
          ? new (window as unknown as { BarcodeDetector: new (o: object) => { detect(v: HTMLVideoElement): Promise<{ rawValue: string }[]> } }).BarcodeDetector({ formats: ["qr_code"] })
          : null;
        const tick = async () => {
          if (!busy.current && v.readyState === 4) {
            if (detector) {
              const codes = await detector.detect(v).catch(() => []);
              if (codes.length) submit(codes[0].rawValue);
            } else {
              canvas.width = v.videoWidth; canvas.height = v.videoHeight;
              const ctx = canvas.getContext("2d")!;
              ctx.drawImage(v, 0, 0);
              const img = ctx.getImageData(0, 0, canvas.width, canvas.height);
              const code = jsQR(img.data, img.width, img.height);
              if (code?.data) submit(code.data);
            }
          }
          raf = requestAnimationFrame(tick);
        };
        raf = requestAnimationFrame(tick);
      } catch { /* camera denied — manual paste still works */ }
    }
    start();
    return () => { cancelAnimationFrame(raf); stream?.getTracks().forEach(t => t.stop()); };
  }, []);

  if (result) {
    return (
      <main className={`min-h-screen flex flex-col items-center justify-center gap-6 text-white ${result.ok ? "bg-emerald-700" : "bg-red-800"}`}>
        <p className="text-4xl font-bold">{result.ok ? "✓" : "✗"}</p>
        <p className="text-xl text-center px-6">{result.msg}</p>
        <button className="rounded-lg bg-black/30 px-6 py-3"
                onClick={() => { setResult(null); busy.current = false; }}>
          {result.ok ? "Done" : "Try again"}
        </button>
        <a className="text-sm underline" href="/me">My attendance</a>
      </main>
    );
  }

  return (
    <main className="min-h-screen flex flex-col items-center justify-center gap-4 bg-zinc-950 text-zinc-100 p-4">
      <h1 className="text-xl font-semibold">Scan the kiosk QR</h1>
      <video ref={videoRef} className="w-full max-w-md rounded-xl bg-black" muted playsInline />
      <details className="w-full max-w-md text-sm text-zinc-400">
        <summary>No camera? Paste code</summary>
        <textarea className="mt-2 w-full rounded-lg bg-zinc-800 p-2 text-xs" rows={4}
                  value={manual} onChange={e => setManual(e.target.value)} />
        <button className="mt-2 rounded-lg bg-emerald-600 px-4 py-2 text-white"
                onClick={() => submit(manual)}>Submit</button>
      </details>
    </main>
  );
}
