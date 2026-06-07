"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api, uploadFile, API_BASE } from "@/lib/api";
import Markdown from "@/components/Markdown";

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

function StatusBadge({ status, step }: { status?: string; step?: number }) {
  const s = status || "created";
  const running = s.startsWith("running:");
  const completed = s === "completed";
  const label = running ? `running · ${s.split(":")[1]}` : s;
  const cls = running
    ? "bg-amber-100 text-amber-800"
    : completed ? "bg-green-100 text-green-800" : "bg-slate-100 text-slate-600";
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${cls}`}>
      {running && <span className="h-2 w-2 rounded-full bg-amber-500 animate-pulse" />}
      {label}{typeof step === "number" ? ` · step ${step}` : ""}
    </span>
  );
}

export default function ReviewWizard({ params }: { params: { id: string } }) {
  const id = params.id;
  const [step, setStep] = useState(0);
  const [review, setReview] = useState<any>(null);
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);
  const [auto, setAuto] = useState(true);
  const [tick, setTick] = useState(0);

  const refresh = useCallback(() => {
    api.getReview(id).then(setReview).catch((e) => setMsg(String(e)));
  }, [id]);

  useEffect(() => { refresh(); }, [refresh]);

  // Live auto-refresh: poll the review and bump a tick so step panels reload —
  // shows progress even when the pipeline is triggered from the CLI.
  useEffect(() => {
    if (!auto) return;
    const t = setInterval(() => { refresh(); setTick((x) => x + 1); }, 4000);
    return () => clearInterval(t);
  }, [auto, refresh]);

  async function run(mode: string) {
    // Guard: re-running a review-generating step over an already-generated
    // review overwrites real content. Require TWO confirmations.
    const generated =
      review?.status === "completed" || Number(review?.current_step ?? 0) >= 9;
    const regenerates = [
      "full_review", "review", "specialized_review", "editorial_decision", "integrity",
    ].includes(mode);
    if (generated && regenerates) {
      if (!window.confirm(
        `This review already has results. Re-running "${mode}" will OVERWRITE the current reviewer/editor content. Continue?`
      )) return;
      if (!window.confirm(
        `Confirm again — regenerate "${mode}" and overwrite the existing results? This cannot be undone.`
      )) return;
    }
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
          <div className="text-xs text-slate-500 flex items-center gap-2">
            <span>{id} · {review?.submission_type}</span>
            <StatusBadge status={review?.status} step={review?.current_step} />
          </div>
        </div>
        <div className="flex items-center gap-3">
          <label className="text-xs text-slate-500 flex items-center gap-1 select-none">
            <input type="checkbox" checked={auto} onChange={(e) => setAuto(e.target.checked)} /> auto-refresh
          </label>
          <button className="btn-primary" disabled={busy} onClick={() => run("full_review")}>
            {busy ? "Working..." : "Run full review"}
          </button>
        </div>
      </div>

      {/* Step nav: reached steps are solid, pending steps are dimmed/italic. */}
      <div className="flex flex-wrap gap-1 items-center">
        {STEPS.map((label, i) => {
          const cur = Number(review?.current_step ?? 0);
          const active = step === i;
          const reached = i <= cur;
          const cls = active
            ? "bg-ieee text-white border-ieee"
            : reached
              ? "border-slate-300 text-slate-700 hover:bg-slate-100"
              : "border-slate-200 text-slate-300 italic hover:bg-slate-50";
          return (
            <button key={i} onClick={() => setStep(i)} title={reached ? "" : "pending"}
              className={`text-xs rounded px-2 py-1 border ${cls}`}>
              {label}
            </button>
          );
        })}
        <button onClick={() => setStep((s) => Math.min(s + 1, STEPS.length - 1))}
          className="text-xs rounded px-3 py-1 bg-petrol text-white hover:opacity-90 ml-1 font-medium"
          disabled={step >= STEPS.length - 1}>
          Next →
        </button>
      </div>

      {msg && <div className="card text-xs text-slate-600">{msg}</div>}

      <StepPanel id={id} step={step} review={review} run={run} busy={busy} onChange={refresh} setMsg={setMsg} tick={tick} />
    </div>
  );
}

function StepPanel({ id, step, review, run, busy, onChange, setMsg, tick }: any) {
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
  if (step === 4) return <VenuesStep id={id} review={review} run={run} busy={busy} setMsg={setMsg} tick={tick} />;
  if (step === 5) return <ArtifactStep id={id} title="Desk-Reject Precheck" mode="desk_reject_precheck" run={run} busy={busy} relpath="venues/desk_reject_precheck.md" />;
  if (step === 6) return <ReviewerProfilesStep />;
  if (step === 7) return <PromptsStep id={id} review={review} run={run} busy={busy} setMsg={setMsg} />;
  if (step === 8) return <ResponsesStep id={id} setMsg={setMsg} />;
  if (step === 9) return <ReviewStep id={id} run={run} busy={busy} tick={tick} />;
  if (step === 10) return <ArtifactStep id={id} title="Integrity Audit" mode="integrity" run={run} busy={busy} relpath="reviewer_outputs/integrity_ai_use_audit.md" />;
  if (step === 11) return <ResultsStep id={id} run={run} busy={busy} tick={tick} />;
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
  const [raw, setRaw] = useState(false);
  function load() { api.artifact(id, relpath).then((r) => setContent(r.content)).catch((e) => setContent(String(e))); }
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [id]);
  return (
    <div className="card space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-ieee-dark">{title}</h2>
        <div className="flex gap-2">
          <button className="btn-ghost" onClick={() => setRaw(!raw)}>{raw ? "Rendered" : "Raw"}</button>
          <button className="btn-ghost" onClick={load}>Reload</button>
          <button className="btn-primary" disabled={busy} onClick={() => run(mode).then(load)}>Run {mode}</button>
        </div>
      </div>
      {raw ? <Mono text={content} /> : <Markdown>{content}</Markdown>}
    </div>
  );
}

function decisionColor(d: string): string {
  const x = (d || "").toLowerCase();
  if (x.includes("accept")) return "bg-green-50 text-green-800 border-green-200";
  if (x.includes("minor")) return "bg-lime-50 text-lime-800 border-lime-200";
  if (x.includes("major")) return "bg-amber-50 text-amber-800 border-amber-200";
  if (x.includes("desk") || x.includes("reject")) return "bg-red-50 text-red-800 border-red-200";
  return "bg-slate-50 text-slate-700 border-slate-200";
}

function ResultsStep({ id, run, busy, tick }: any) {
  const [sum, setSum] = useState<any>(null);
  const [editor, setEditor] = useState("");
  function load() {
    api.summary(id).then(setSum).catch(() => {});
    api.artifact(id, "editor/editor_decision.md").then((r) => setEditor(r.content)).catch(() => setEditor(""));
  }
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [id, tick]);
  const reviewers = sum?.reviewers || [];
  return (
    <div className="space-y-4">
      <div className="card space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-ieee-dark">Results — Editor decision</h2>
          <div className="flex gap-2">
            <button className="btn-ghost" onClick={load}>Reload</button>
            <button className="btn-primary" disabled={busy} onClick={() => run("editorial_decision").then(load)}>Run editor</button>
          </div>
        </div>
        <div className={`decision-banner ${decisionColor(sum?.editor?.decision)}`}>
          Decision: {sum?.editor?.decision || "—"}
          <span className="ml-2 text-xs font-normal">({sum?.editor?.engine} · {sum?.editor?.mode})</span>
        </div>
      </div>

      <div className="card">
        <h3 className="font-semibold text-slate-700 mb-2">Reviewer recommendations</h3>
        <div className="table-wrap">
          <table className="w-full">
            <thead><tr><th className="th">Reviewer</th><th className="th">Engine / mode</th><th className="th">Recommendation</th></tr></thead>
            <tbody>
              {reviewers.map((r: any) => (
                <tr key={r.name}>
                  <td className="td"><div className="font-medium">{r.name}</div><div className="text-xs text-slate-400">{r.kind}</div></td>
                  <td className="td"><span className={`badge ${r.is_real ? "" : "opacity-60"}`}>{r.engine} · {r.mode}</span></td>
                  <td className="td text-sm">{r.recommendation}</td>
                </tr>
              ))}
              {reviewers.length === 0 && (
                <tr><td className="td text-slate-500" colSpan={3}>No reviewers yet — run step 9 (Autonomous Review).</td></tr>
              )}
            </tbody>
          </table>
        </div>
        {sum?.integrity && <p className="text-xs text-slate-500 mt-2">Integrity audit: {sum.integrity.engine} · {sum.integrity.mode}</p>}
      </div>

      <div className="card">
        <h3 className="font-semibold text-slate-700 mb-2">Editor decision (full)</h3>
        <Markdown>{editor}</Markdown>
      </div>
    </div>
  );
}

function VenuesStep({ id, review, run, busy, setMsg, tick }: any) {
  const [data, setData] = useState<any>({ candidates: [], detected_area_labels: [] });
  const [selected, setSelected] = useState<string[]>([]);
  const [showAll, setShowAll] = useState(false);
  const initRef = useRef(false);
  function load() { api.venueCandidates(id).then(setData).catch((e) => setMsg(String(e))); }
  // Candidates may refresh on the auto-refresh tick.
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [id, tick]);
  // Initialise the selection from saved metadata ONCE, so auto-refresh never
  // wipes the checkboxes the user is editing before they hit Save.
  useEffect(() => {
    if (!initRef.current && review?.metadata) {
      setSelected(review.metadata.selected_venues || []);
      initRef.current = true;
    }
  }, [review]);

  function toggle(vid: string) {
    setSelected((s) => s.includes(vid) ? s.filter((x) => x !== vid) : [...s, vid]);
  }
  async function save() {
    await api.selectVenues(id, selected);
    setMsg(`Saved ${selected.length} selected venues`);
  }

  const cands: any[] = data.candidates || [];
  const relevant = cands.filter((c) => c.score > 0);
  const shown = showAll ? cands : (relevant.length ? relevant : cands.slice(0, 8));

  return (
    <div className="card space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-semibold text-ieee-dark">Candidate venues</h2>
          <div className="text-xs text-slate-500">
            Detected areas: {(data.detected_area_labels || []).join(" · ") || "run Extraction + Area & Paper Type first"}
          </div>
        </div>
        <div className="flex gap-2">
          <button className="btn-ghost" onClick={() => run("discover_venues").then(load)} disabled={busy}>Re-rank</button>
          <button className="btn-primary" onClick={save}>Save selection ({selected.length})</button>
        </div>
      </div>
      {relevant.length === 0 && (
        <p className="text-xs text-amber-600">No venues match the detected areas yet — run Extraction + Area &amp; Paper Type first (or “Show all”).</p>
      )}
      <div className="table-wrap max-h-[28rem] overflow-auto">
        <table className="w-full">
          <thead><tr><th className="th"></th><th className="th">Match</th><th className="th">Venue</th><th className="th">Q1 access</th><th className="th">Quartile/Rank</th><th className="th">Speed</th></tr></thead>
          <tbody>
            {shown.map((v) => (
              <tr key={v.venue_id} className={v.score > 0 ? "" : "opacity-50"}>
                <td className="td"><input type="checkbox" checked={selected.includes(v.venue_id)} onChange={() => toggle(v.venue_id)} /></td>
                <td className="td">{v.score > 0
                  ? <span className="inline-block rounded-full px-2 py-0.5 text-xs font-medium bg-green-100 text-green-800">✓ {v.score}</span>
                  : <span className="text-xs text-slate-400">—</span>}</td>
                <td className="td"><div className="font-medium">{v.name}</div><div className="text-xs text-slate-500">{v.acronym} · {(v.family_labels || []).join("; ")}</div></td>
                <td className="td">{v.q1_accessibility_class}</td>
                <td className="td text-xs">{v.quartile_or_rank}</td>
                <td className="td">{v.publication_speed_category}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <button className="text-xs text-ieee hover:underline" onClick={() => setShowAll(!showAll)}>
        {showAll ? "Show only matches" : `Show all ${cands.length} venues`}
      </button>
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

function ReviewStep({ id, run, busy, tick }: any) {
  const [tree, setTree] = useState<string[]>([]);
  const [sel, setSel] = useState("");
  const [content, setContent] = useState("");
  function loadTree() { api.tree(id).then((r) => setTree(r.files.filter((f: string) => f.startsWith("reviewer_outputs/")))).catch(() => {}); }
  useEffect(() => { loadTree(); /* eslint-disable-next-line */ }, [id, tick]);
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
        <div className="col-span-2">{content ? <Markdown>{content}</Markdown> : <p className="text-xs text-slate-400">Select a reviewer to read it.</p>}</div>
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
