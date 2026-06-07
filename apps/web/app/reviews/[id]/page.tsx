"use client";

import { useCallback, useEffect, useState } from "react";
import { api, uploadFile, API_BASE } from "@/lib/api";

const STEPS = [
  "0. Create / Metadata", "1. Upload", "2. Extraction", "3. Area & Paper Type",
  "4. Venues", "5. Desk-Reject Precheck", "6. Reviewer Profiles", "7. External Prompts",
  "8. External Responses", "9. Autonomous Review", "10. Integrity Audit",
  "11. Editor Decision", "12. Revision Plan", "13. Export",
];

function Mono({ text }: { text: string }) {
  return (
    <pre className="mt-3 max-h-[28rem] overflow-auto rounded-md bg-slate-50 border border-slate-200 p-3 text-xs whitespace-pre-wrap">
      {text || "(empty)"}
    </pre>
  );
}

export default function ReviewWizard({ params }: { params: { id: string } }) {
  const id = params.id;
  const [step, setStep] = useState(0);
  const [review, setReview] = useState<any>(null);
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(() => {
    api.getReview(id).then(setReview).catch((e) => setMsg(String(e)));
  }, [id]);

  useEffect(() => { refresh(); }, [refresh]);

  async function run(mode: string) {
    setBusy(true); setMsg(`Running ${mode}...`);
    try {
      const r = await api.runPipeline(id, mode);
      setMsg(`Done: ${mode}. Outputs: ${(r.outputs || []).join(", ") || "(none)"}${r.warnings?.length ? " | warnings: " + r.warnings.join("; ") : ""}`);
      refresh();
    } catch (e) { setMsg(String(e)); }
    setBusy(false);
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-ieee-dark">{review?.title || id}</h1>
          <div className="text-xs text-slate-500">{id} · {review?.status} · {review?.submission_type}</div>
        </div>
        <button className="btn-primary" disabled={busy} onClick={() => run("full_review")}>
          {busy ? "Working..." : "Run full review"}
        </button>
      </div>

      {/* Step nav */}
      <div className="flex flex-wrap gap-1">
        {STEPS.map((label, i) => (
          <button key={i} onClick={() => setStep(i)}
            className={`text-xs rounded px-2 py-1 border ${step === i ? "bg-ieee text-white border-ieee" : "border-slate-300 text-slate-600 hover:bg-slate-100"}`}>
            {label}
          </button>
        ))}
      </div>

      {msg && <div className="card text-xs text-slate-600">{msg}</div>}

      <StepPanel id={id} step={step} review={review} run={run} busy={busy} onChange={refresh} setMsg={setMsg} />
    </div>
  );
}

function StepPanel({ id, step, review, run, busy, onChange, setMsg }: any) {
  if (step === 0) {
    return (
      <div className="card">
        <h2 className="font-semibold text-ieee-dark mb-2">Metadata</h2>
        <Mono text={JSON.stringify(review?.metadata || {}, null, 2)} />
      </div>
    );
  }
  if (step === 1) return <UploadStep id={id} onChange={onChange} setMsg={setMsg} />;
  if (step === 2) return <ArtifactStep id={id} title="Extraction" mode="extract" run={run} busy={busy} relpath="extracted/paper_extraction.md" />;
  if (step === 3) return <ArtifactStep id={id} title="Area & Paper Type" mode="classify" run={run} busy={busy} relpath="extracted/classification.md" />;
  if (step === 4) return <VenuesStep id={id} review={review} run={run} busy={busy} setMsg={setMsg} />;
  if (step === 5) return <ArtifactStep id={id} title="Desk-Reject Precheck" mode="desk_reject_precheck" run={run} busy={busy} relpath="venues/desk_reject_precheck.md" />;
  if (step === 6) return <ReviewerProfilesStep />;
  if (step === 7) return <PromptsStep id={id} review={review} run={run} busy={busy} setMsg={setMsg} />;
  if (step === 8) return <ResponsesStep id={id} setMsg={setMsg} />;
  if (step === 9) return <ReviewStep id={id} run={run} busy={busy} />;
  if (step === 10) return <ArtifactStep id={id} title="Integrity Audit" mode="integrity" run={run} busy={busy} relpath="reviewer_outputs/integrity_ai_use_audit.md" />;
  if (step === 11) return <ArtifactStep id={id} title="Editor Decision" mode="editorial_decision" run={run} busy={busy} relpath="editor/editor_decision.md" />;
  if (step === 12) return <ArtifactStep id={id} title="Revision Plan" mode="editorial_decision" run={run} busy={busy} relpath="editor/revision_plan.md" />;
  if (step === 13) return <ExportStep id={id} run={run} busy={busy} />;
  return null;
}

function UploadStep({ id, onChange, setMsg }: any) {
  const [kind, setKind] = useState("manuscript");
  const [busy, setBusy] = useState(false);
  const [report, setReport] = useState<any>(null);
  async function onFile(e: any) {
    const f = e.target.files?.[0]; if (!f) return;
    setBusy(true); setMsg("Uploading...");
    try {
      const r = await uploadFile(`/reviews/${id}/uploads`, f, { kind });
      setReport(r); setMsg(r.ok ? "Upload OK" : "Upload rejected"); onChange();
    } catch (err) { setMsg(String(err)); }
    setBusy(false);
  }
  return (
    <div className="card space-y-3">
      <h2 className="font-semibold text-ieee-dark">Upload manuscript / files</h2>
      <p className="text-xs text-slate-500">Accepted: PDF, DOCX, MD, TeX, ZIP (LaTeX), BibTeX, CSV, YAML, JSON. Validated for type, size and safe ZIP paths.</p>
      <select className="input max-w-xs" value={kind} onChange={(e) => setKind(e.target.value)}>
        <option value="manuscript">manuscript</option>
        <option value="previous_review">previous_review</option>
        <option value="author_response">author_response</option>
      </select>
      <input type="file" onChange={onFile} disabled={busy} className="block text-sm" />
      {report && <Mono text={JSON.stringify(report, null, 2)} />}
    </div>
  );
}

function ArtifactStep({ id, title, mode, run, busy, relpath }: any) {
  const [content, setContent] = useState("");
  function load() { api.artifact(id, relpath).then((r) => setContent(r.content)).catch((e) => setContent(String(e))); }
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [id]);
  return (
    <div className="card space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-ieee-dark">{title}</h2>
        <div className="flex gap-2">
          <button className="btn-ghost" onClick={load}>Reload</button>
          <button className="btn-primary" disabled={busy} onClick={() => run(mode).then(load)}>Run {mode}</button>
        </div>
      </div>
      <Mono text={content} />
    </div>
  );
}

function VenuesStep({ id, review, run, busy, setMsg }: any) {
  const [venues, setVenues] = useState<any[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  useEffect(() => {
    api.listVenues().then(setVenues).catch((e) => setMsg(String(e)));
    setSelected(review?.metadata?.selected_venues || []);
  }, [review, setMsg]);
  function toggle(vid: string) {
    setSelected((s) => s.includes(vid) ? s.filter((x) => x !== vid) : [...s, vid]);
  }
  async function save() {
    await api.selectVenues(id, selected);
    setMsg(`Saved ${selected.length} selected venues`);
  }
  return (
    <div className="card space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-ieee-dark">Venues ({venues.length})</h2>
        <div className="flex gap-2">
          <button className="btn-ghost" onClick={() => run("discover_venues")} disabled={busy}>Discover candidates</button>
          <button className="btn-primary" onClick={save}>Save selection ({selected.length})</button>
        </div>
      </div>
      <div className="table-wrap max-h-[28rem] overflow-auto">
        <table className="w-full">
          <thead><tr><th className="th"></th><th className="th">Venue</th><th className="th">Q1 access</th><th className="th">Quartile/Rank</th><th className="th">Speed</th></tr></thead>
          <tbody>
            {venues.map((v) => (
              <tr key={v.venue_id}>
                <td className="td"><input type="checkbox" checked={selected.includes(v.venue_id)} onChange={() => toggle(v.venue_id)} /></td>
                <td className="td"><div className="font-medium">{v.name}</div><div className="text-xs text-slate-500">{v.acronym} · {v.venue_id}</div></td>
                <td className="td">{v.q1_accessibility_class}</td>
                <td className="td text-xs">{v.quartile_or_rank}</td>
                <td className="td">{v.publication_speed_category}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ReviewerProfilesStep() {
  const [data, setData] = useState<any>(null);
  useEffect(() => { api.reviewerProfiles().then(setData).catch(() => {}); }, []);
  if (!data) return <div className="card text-sm text-slate-500">Loading profiles...</div>;
  const groups: [string, any[]][] = [["Main", data.main_reviewers], ["Specialized", data.specialized_reviewers], ["Auditors", data.auditors]];
  return (
    <div className="card space-y-4">
      <h2 className="font-semibold text-ieee-dark">Reviewer profiles</h2>
      {groups.map(([name, list]) => (
        <div key={name}>
          <div className="text-sm font-semibold text-slate-600 mb-1">{name}</div>
          <ul className="space-y-1">
            {list?.map((p: any) => (
              <li key={p.id} className="text-sm flex items-center gap-2">
                <input type="checkbox" defaultChecked={p.default_enabled} /> <span className="font-medium">{p.id}</span>
                <span className="text-slate-500">— {p.title}</span>
              </li>
            ))}
          </ul>
        </div>
      ))}
      <p className="text-xs text-slate-500">Specialized reviewers auto-activate based on detected areas when you run the pipeline.</p>
    </div>
  );
}

function PromptsStep({ id, review, run, busy, setMsg }: any) {
  const [content, setContent] = useState("");
  const [profiles, setProfiles] = useState<string[]>([]);
  const [status, setStatus] = useState<any>({ engines: {}, query_engines: [] });
  const [venue, setVenue] = useState("");
  const [profile, setProfile] = useState("");
  const [engine, setEngine] = useState("");
  const [running, setRunning] = useState(false);
  const [preview, setPreview] = useState("");

  const selectedVenues: string[] = review?.metadata?.selected_venues || [];

  function load() { api.externalPrompts(id).then((r) => setContent(r.index)).catch((e) => setContent(String(e))); }
  useEffect(() => {
    load();
    api.reviewerProfiles().then((r) => {
      const all = [...r.main_reviewers, ...r.specialized_reviewers].map((p: any) => p.id);
      setProfiles(all); setProfile(all[0] || "");
    }).catch(() => {});
    api.engineStatus().then((s) => {
      setStatus(s);
      const firstAvail = (s.query_engines || []).find((e: string) => s.engines?.[e]?.available);
      setEngine(firstAvail || s.query_engines?.[0] || "");
    }).catch(() => {});
    // eslint-disable-next-line
  }, [id]);
  useEffect(() => { if (selectedVenues.length && !venue) setVenue(selectedVenues[0]); }, [selectedVenues, venue]);

  async function execute() {
    if (!venue || !profile || !engine) { setMsg("Pick venue, reviewer and engine first."); return; }
    setRunning(true); setPreview(""); setMsg(`Running ${engine} CLI...`);
    try {
      const r = await api.runQuery(id, { venue_id: venue, reviewer_profile: profile, engine });
      setPreview(r.error ? `ERROR: ${r.error}` : r.preview);
      setMsg(r.ok ? `Saved: ${r.stored_path}` : `Engine error: ${r.error}`);
      load();
    } catch (e) { setMsg(String(e)); }
    setRunning(false);
  }

  return (
    <div className="card space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-ieee-dark">External Prompts</h2>
        <button className="btn-ghost" disabled={busy} onClick={() => run("generate_external_prompts").then(load)}>Generate prompts</button>
      </div>
      <p className="text-xs text-slate-500">Generate prompts per selected venue × reviewer × engine, or run a query directly via the engine CLI (Claude / Codex / Ollama / Gemini).</p>

      <div className="rounded-md border border-ieee-light bg-ieee-light/40 p-3 space-y-2">
        <div className="text-sm font-semibold text-ieee-dark">Execute query (engine CLI)</div>
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-2">
          <select className="input" value={venue} onChange={(e) => setVenue(e.target.value)}>
            <option value="">venue…</option>
            {(selectedVenues.length ? selectedVenues : [venue].filter(Boolean)).map((v) => <option key={v} value={v}>{v}</option>)}
          </select>
          <select className="input" value={profile} onChange={(e) => setProfile(e.target.value)}>
            {profiles.map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
          <select className="input" value={engine} onChange={(e) => setEngine(e.target.value)}>
            {(status.query_engines || []).map((e: string) => {
              const av = status.engines?.[e]?.available;
              return <option key={e} value={e} disabled={!av}>{e}{av ? "" : " (not installed)"}</option>;
            })}
          </select>
          <button className="btn-primary justify-center" disabled={running} onClick={execute}>
            {running ? "Running…" : "Execute query"}
          </button>
        </div>
        {selectedVenues.length === 0 && <p className="text-xs text-amber-600">Tip: select venues in Step 4 first.</p>}
        {preview && <Mono text={preview} />}
      </div>

      <Mono text={content} />
    </div>
  );
}

function ResponsesStep({ id, setMsg }: any) {
  const [content, setContent] = useState("");
  function load() { api.externalResponses(id).then((r) => setContent(r.index)).catch(() => {}); }
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [id]);
  async function onFile(e: any) {
    const f = e.target.files?.[0]; if (!f) return;
    setMsg("Importing response...");
    try { await uploadFile(`/reviews/${id}/external-responses`, f); setMsg("Imported"); load(); }
    catch (err) { setMsg(String(err)); }
  }
  return (
    <div className="card space-y-3">
      <h2 className="font-semibold text-ieee-dark">External Responses</h2>
      <p className="text-xs text-slate-500">Upload an AI response (MD, PDF or DOCX). Engine/reviewer/venue are auto-detected from the filename.</p>
      <input type="file" onChange={onFile} className="block text-sm" />
      <Mono text={content} />
    </div>
  );
}

function ReviewStep({ id, run, busy }: any) {
  const [tree, setTree] = useState<string[]>([]);
  const [sel, setSel] = useState("");
  const [content, setContent] = useState("");
  function loadTree() { api.tree(id).then((r) => setTree(r.files.filter((f: string) => f.startsWith("reviewer_outputs/")))).catch(() => {}); }
  useEffect(() => { loadTree(); /* eslint-disable-next-line */ }, [id]);
  function open(f: string) { setSel(f); api.artifact(id, f).then((r) => setContent(r.content)); }
  return (
    <div className="card space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-ieee-dark">Autonomous Review</h2>
        <div className="flex gap-2">
          <button className="btn-ghost" disabled={busy} onClick={() => run("review").then(loadTree)}>Run main reviewers</button>
          <button className="btn-primary" disabled={busy} onClick={() => run("specialized_review").then(loadTree)}>Run specialized</button>
        </div>
      </div>
      <div className="grid grid-cols-3 gap-3">
        <ul className="col-span-1 text-xs space-y-1 max-h-80 overflow-auto">
          {tree.map((f) => (
            <li key={f}><button className={`text-left hover:underline ${sel === f ? "text-ieee font-medium" : "text-slate-600"}`} onClick={() => open(f)}>{f.replace("reviewer_outputs/", "")}</button></li>
          ))}
        </ul>
        <div className="col-span-2"><Mono text={content} /></div>
      </div>
    </div>
  );
}

function ExportStep({ id, run, busy }: any) {
  return (
    <div className="card space-y-3">
      <h2 className="font-semibold text-ieee-dark">Export</h2>
      <p className="text-xs text-slate-500">Assembles the final package (Markdown always; PDF best-effort) and zips it.</p>
      <div className="flex gap-2">
        <button className="btn-primary" disabled={busy} onClick={() => run("export")}>Build export package</button>
        <a className="btn-ghost" href={`${API_BASE}/reviews/${id}/export/download`} target="_blank" rel="noreferrer">Download zip</a>
      </div>
    </div>
  );
}
