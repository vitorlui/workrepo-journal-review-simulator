"use client";

import { useEffect, useState } from "react";
import { api, uploadFile } from "@/lib/api";

export default function VenuesPage() {
  const [venues, setVenues] = useState<any[]>([]);
  const [msg, setMsg] = useState("");
  const [reports, setReports] = useState<string[]>([]);
  const [name, setName] = useState("");
  const [acronym, setAcronym] = useState("");

  function load() {
    api.listVenues().then(setVenues).catch((e) => setMsg(String(e)));
    api.vdReports().then((r) => setReports(r.reports)).catch(() => {});
  }
  useEffect(load, []);

  async function importVD(e: any) {
    const f = e.target.files?.[0]; if (!f) return;
    setMsg("Importing venue discovery response...");
    try {
      const r = await uploadFile("/venue-discovery/import", f);
      setMsg(`Imported ${r.imported} venues (format: ${r.detected_format}, collisions resolved: ${r.collisions_resolved}). Report: ${r.report_path}`);
      load();
    } catch (err) { setMsg(String(err)); }
  }

  async function reimportRaw() {
    setMsg("Re-importing everything in venue_discovery/raw/...");
    try { const r = await api.vdImportRawDir(); setMsg(`Processed ${r.files_processed} raw files.`); load(); }
    catch (err) { setMsg(String(err)); }
  }

  async function createVenue() {
    if (!name) return;
    try { await api.createVenue({ name, acronym: acronym || "UNKNOWN", type: "journal" }); setName(""); setAcronym(""); setMsg("Venue created"); load(); }
    catch (err) { setMsg(String(err)); }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-ieee-dark">Venues ({venues.length})</h1>
      {msg && <div className="card text-xs text-slate-600">{msg}</div>}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card space-y-2">
          <h2 className="font-semibold text-ieee-dark text-sm">Import venue discovery (Perplexity)</h2>
          <p className="text-xs text-slate-500">Upload a Markdown table or CSV response. Format auto-detected; venue IDs are slug-based to avoid collisions.</p>
          <input type="file" accept=".csv,.md,.txt,.tsv" onChange={importVD} className="block text-sm" />
          <button className="btn-ghost w-full justify-center" onClick={reimportRaw}>Re-import raw/ folder</button>
        </div>

        <div className="card space-y-2">
          <h2 className="font-semibold text-ieee-dark text-sm">Import venue CSV</h2>
          <p className="text-xs text-slate-500">Same engine as venue discovery (accepts the 39-column venue schema).</p>
          <input type="file" accept=".csv,.md" onChange={importVD} className="block text-sm" />
        </div>

        <div className="card space-y-2">
          <h2 className="font-semibold text-ieee-dark text-sm">Create venue manually</h2>
          <input className="input" placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} />
          <input className="input" placeholder="Acronym" value={acronym} onChange={(e) => setAcronym(e.target.value)} />
          <button className="btn-primary w-full justify-center" onClick={createVenue}>Create</button>
        </div>
      </div>

      {reports.length > 0 && (
        <div className="card">
          <h2 className="font-semibold text-ieee-dark text-sm mb-2">Import reports</h2>
          <ul className="text-xs text-slate-600 space-y-1">
            {reports.map((r) => <li key={r}>{r}</li>)}
          </ul>
        </div>
      )}

      <div className="table-wrap">
        <table className="w-full">
          <thead><tr><th className="th">Venue</th><th className="th">Type</th><th className="th">Families</th><th className="th">Q1 access</th><th className="th">Quartile/Rank</th><th className="th">Speed</th><th className="th">Rigor</th></tr></thead>
          <tbody>
            {venues.map((v) => (
              <tr key={v.venue_id}>
                <td className="td"><div className="font-medium">{v.name}</div><div className="text-xs text-slate-500">{v.acronym} · {v.venue_id}</div></td>
                <td className="td">{v.type}</td>
                <td className="td text-xs">{(v.family_labels || []).join("; ")}</td>
                <td className="td">{v.q1_accessibility_class}</td>
                <td className="td text-xs">{v.quartile_or_rank}</td>
                <td className="td">{v.publication_speed_category}</td>
                <td className="td">{v.review_rigor}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
