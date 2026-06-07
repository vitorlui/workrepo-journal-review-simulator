"use client";

import { useEffect, useState } from "react";
import { api, API_BASE } from "@/lib/api";

export default function SettingsPage() {
  const [health, setHealth] = useState<any>(null);
  const [engines, setEngines] = useState<any>(null);
  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth({ status: "unreachable" }));
    api.aiEngines().then(setEngines).catch(() => {});
  }, []);
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-ieee-dark">Settings</h1>
      <div className="card space-y-2 text-sm">
        <div><span className="text-slate-500">API base URL:</span> <code>{API_BASE}</code></div>
        <div><span className="text-slate-500">API status:</span> <span className="badge">{health?.status || "..."}</span></div>
        <div><span className="text-slate-500">Default internal engine:</span> {engines?.default_engine || "template"}</div>
      </div>
      <div className="card text-sm text-slate-600 space-y-2">
        <h2 className="font-semibold text-ieee-dark">Architecture</h2>
        <p>Markdown/YAML is the semantic memory; the database only indexes and tracks workflow state. The internal pipeline runs offline by default (template engine); Claude/Ollama are pluggable seams.</p>
        <p className="text-xs text-slate-400">Max clarification iterations per agent default to 3 (config/pipeline.yaml). Upload limits and allowed types live in config/upload_policy.yaml.</p>
      </div>
    </div>
  );
}
