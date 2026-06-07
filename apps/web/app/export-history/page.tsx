"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, API_BASE } from "@/lib/api";

export default function ExportHistoryPage() {
  const [rows, setRows] = useState<any[]>([]);
  useEffect(() => { api.listReviews().then(setRows).catch(() => {}); }, []);
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-ieee-dark">Export / History</h1>
      <p className="text-sm text-slate-600">Full history of every review. Build the package from the review&apos;s Export step, then download here.</p>
      <div className="table-wrap">
        <table className="w-full">
          <thead><tr><th className="th">Review ID</th><th className="th">Title</th><th className="th">Status</th><th className="th">Decision</th><th className="th">Actions</th></tr></thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.review_id}>
                <td className="td"><Link className="text-ieee hover:underline" href={`/reviews/${r.review_id}`}>{r.review_id}</Link></td>
                <td className="td">{r.title}</td>
                <td className="td"><span className="badge">{r.status}</span></td>
                <td className="td">{r.final_decision || "—"}</td>
                <td className="td">
                  <a className="text-ieee hover:underline text-xs" href={`${API_BASE}/reviews/${r.review_id}/export/download`} target="_blank" rel="noreferrer">download zip</a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
