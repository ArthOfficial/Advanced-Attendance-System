"use client";
import { useEffect } from "react";
import { roleFromToken } from "@/lib/api";

// / is just a router: send everyone straight to their role's home.
export default function Home() {
  useEffect(() => {
    const role = roleFromToken();
    window.location.replace(
      !role ? "/login" : role === "admin" ? "/admin" : role === "kiosk" ? "/kiosk" : "/me");
  }, []);
  return (
    <main className="min-h-screen flex items-center justify-center bg-zinc-950 text-zinc-500">
      Redirecting…
    </main>
  );
}
