"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function ReviewerProfilesPage() {
  const [data, setData] = useState<any>(null);
  const [err, setErr] = useState("");
  useEffect(() => { api.reviewerProfiles().then(setData).catch((e) => setErr(String(e))); }, []);

  const groups: [string, any[]][] = data
    ? [["Main reviewers", data.main_reviewers], ["Specialized reviewers", data.specialized_reviewers], ["Auditors", data.auditors]]
    : [];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-ieee-dark">Reviewer Profiles</h1>
      {err && <div className="card text-red-600 text-sm">{err}</div>}
      {groups.map(([name, list]) => (
        <div key={name} className="card">
          <h2 className="font-semibold text-ieee-dark mb-3">{name}</h2>
          <div className="space-y-2">
            {list?.map((p: any) => (
              <div key={p.id} className="border-b border-slate-100 pb-2">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{p.id}</span>
                  {p.has_profile_md ? <span className="badge">profile .md</span> : <span className="text-xs text-amber-600">no profile</span>}
                </div>
                <div className="text-sm text-slate-600">{p.title}</div>
                {p.activation_areas?.length > 0 && (
                  <div className="text-xs text-slate-400">activates on: {p.activation_areas.join(", ")}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
