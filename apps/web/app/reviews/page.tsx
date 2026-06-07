"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

export default function ReviewsPage() {
  const [rows, setRows] = useState<any[]>([]);
  const [err, setErr] = useState("");

  useEffect(() => {
    api.listReviews().then(setRows).catch((e) => setErr(String(e)));
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-ieee-dark">Reviews</h1>
        <Link href="/reviews/new" className="btn-primary">+ New Review</Link>
      </div>
      {err && <div className="card text-red-600 text-sm">{err}</div>}
      <div className="table-wrap">
        <table className="w-full">
          <thead>
            <tr><th className="th">Review ID</th><th className="th">Title</th><th className="th">Type</th><th className="th">Paper type</th><th className="th">Areas</th><th className="th">Status</th></tr>
          </thead>
          <tbody>
            {rows.length === 0 && (
              <tr><td className="td text-slate-500" colSpan={6}>No reviews yet.</td></tr>
            )}
            {rows.map((r) => (
              <tr key={r.review_id}>
                <td className="td"><Link className="text-ieee hover:underline" href={`/reviews/${r.review_id}`}>{r.review_id}</Link></td>
                <td className="td">{r.title}</td>
                <td className="td">{r.submission_type}</td>
                <td className="td">{r.paper_type}</td>
                <td className="td">{Array.isArray(r.detected_areas) ? r.detected_areas.join(", ") : ""}</td>
                <td className="td"><span className="badge">{r.status}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
