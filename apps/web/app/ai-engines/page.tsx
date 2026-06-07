"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function AiEnginesPage() {
  const [data, setData] = useState<any>(null);
  const [err, setErr] = useState("");
  useEffect(() => { api.aiEngines().then(setData).catch((e) => setErr(String(e))); }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-ieee-dark">AI Engines</h1>
      {err && <div className="card text-red-600 text-sm">{err}</div>}
      {data && (
        <>
          <div className="card">
            <h2 className="font-semibold text-ieee-dark mb-2">Internal pipeline engine</h2>
            <p className="text-sm">Default: <span className="badge">{data.default_engine}</span> (offline Markdown scaffolding; no API keys).</p>
            <ul className="mt-2 text-sm text-slate-600 space-y-1">
              {Object.entries(data.internal_engines || {}).map(([k, v]: any) => (
                <li key={k}><span className="font-medium">{k}</span> — {v.description}</li>
              ))}
            </ul>
          </div>
          <div className="card">
            <h2 className="font-semibold text-ieee-dark mb-2">External engines (manual prompt / response)</h2>
            <div className="flex flex-wrap gap-2">
              {(data.external_engines || []).map((e: any) => <span key={e.id} className="badge">{e.name}</span>)}
            </div>
            <div className="mt-3 text-xs text-slate-500">Modes: {(data.internal_modes || []).join(", ")}</div>
          </div>
        </>
      )}
    </div>
  );
}
