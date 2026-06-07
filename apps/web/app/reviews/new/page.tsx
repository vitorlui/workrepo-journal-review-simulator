"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

const SUBMISSION_TYPES = [
  "new_submission",
  "resubmission",
  "minor revision",
  "major revision",
  "reject and resubmit",
  "post-review revision",
  "camera-ready",
];

export default function NewReviewPage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [type, setType] = useState("new_submission");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  async function submit() {
    setBusy(true);
    setErr("");
    try {
      const r = await api.createReview(title || "UNKNOWN", type);
      router.push(`/reviews/${r.review_id}`);
    } catch (e) {
      setErr(String(e));
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6 max-w-xl">
      <h1 className="text-2xl font-semibold text-ieee-dark">New Review</h1>
      <div className="card space-y-4">
        <div>
          <label className="text-sm font-medium text-slate-700">Working title</label>
          <input className="input mt-1" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Lightweight FAS for edge devices" />
        </div>
        <div>
          <label className="text-sm font-medium text-slate-700">Submission type</label>
          <select className="input mt-1" value={type} onChange={(e) => setType(e.target.value)}>
            {SUBMISSION_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
        {err && <p className="text-sm text-red-600">{err}</p>}
        <button className="btn-primary" disabled={busy} onClick={submit}>
          {busy ? "Creating..." : "Create review"}
        </button>
        <p className="text-xs text-slate-500">
          A unique review ID (REV-YYYYMMDD-HHMMSS-XXXXXX) and its documental folder tree will be created.
        </p>
      </div>
    </div>
  );
}
