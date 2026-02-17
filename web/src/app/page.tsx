"use client";

import { useEffect, useState } from "react";

/**
 * GB Guide — Home Page
 *
 * Fetches the backend health-check endpoint to prove
 * full-stack connectivity (Next.js → FastAPI → Postgres).
 */

interface HealthResponse {
  status: string;
}

export default function Home() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const API_URL =
      process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    fetch(`${API_URL}/api/health`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data: HealthResponse) => {
        setHealth(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 font-sans">
      <main className="flex flex-col items-center gap-8 text-center">
        {/* ── Logo / Title ──────────────────────────────────── */}
        <div className="flex flex-col items-center gap-3">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-400 to-cyan-500 text-2xl font-black text-white shadow-lg shadow-emerald-500/25">
            GB
          </div>
          <h1 className="text-4xl font-bold tracking-tight text-white">
            GB Guide
          </h1>
          <p className="text-lg text-slate-400">
            Full-Stack Connectivity Check
          </p>
        </div>

        {/* ── Health Status Card ────────────────────────────── */}
        <div className="w-80 rounded-2xl border border-slate-700/50 bg-slate-800/50 p-6 shadow-xl backdrop-blur-sm">
          <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-400">
            Backend Health
          </h2>

          {loading && (
            <div className="flex items-center justify-center gap-3">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-slate-600 border-t-emerald-400" />
              <span className="text-slate-300">Connecting…</span>
            </div>
          )}

          {health && (
            <div className="flex flex-col items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-500/10">
                <svg
                  className="h-6 w-6 text-emerald-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={2.5}
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M4.5 12.75l6 6 9-13.5"
                  />
                </svg>
              </div>
              <p className="text-lg font-medium text-emerald-400">
                Status: {health.status}
              </p>
              <code className="rounded-lg bg-slate-900 px-4 py-2 text-xs text-slate-300">
                GET /api/health → {JSON.stringify(health)}
              </code>
            </div>
          )}

          {error && (
            <div className="flex flex-col items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-red-500/10">
                <svg
                  className="h-6 w-6 text-red-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={2.5}
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </div>
              <p className="text-lg font-medium text-red-400">
                Connection Failed
              </p>
              <code className="rounded-lg bg-slate-900 px-4 py-2 text-xs text-red-300">
                {error}
              </code>
              <p className="mt-1 text-xs text-slate-500">
                Make sure the backend is running on port 8000
              </p>
            </div>
          )}
        </div>

        {/* ── Instructions ─────────────────────────────────── */}
        <div className="max-w-md text-sm leading-relaxed text-slate-500">
          Run{" "}
          <code className="rounded bg-slate-800 px-2 py-0.5 text-emerald-400">
            docker-compose up --build
          </code>{" "}
          to start all services.
        </div>
      </main>
    </div>
  );
}
