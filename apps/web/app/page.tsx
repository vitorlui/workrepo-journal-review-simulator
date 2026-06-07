"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

export default function Dashboard() {
  const [data, setData] = useState<any>(null);
  const [err, setErr] = useState<string>("");

  useEffect(() => {
    api.dashboard().then(setData).catch((e) => setErr(String(e)));
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-ieee-dark">Dashboard</h1>
        <Link href="/reviews/new" className="btn-primary">+ New Review</Link>
      </div>

      {err && <div className="card text-red-600 text-sm">API error: {err}<br/>Is the backend running at {api.base}?</div>}

      {data && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="card">
              <div className="text-3xl font-bold text-ieee">{data.reviews_total}</div>
              <div className="text-sm text-slate-500">Reviews</div>
            </div>
            <div className="card">
              <div className="text-3xl font-bold text-ieee">{data.venues_total}</div>
              <div className="text-sm text-slate-500">Venues indexed</div>
            </div>
            <div className="card">
              <div className="text-3xl font-bold text-ieee">
                {Object.keys(data.reviews_by_status || {}).length}
              </div>
              <div className="text-sm text-slate-500">Distinct statuses</div>
            </div>
          </div>

          <div className="card">
            <h2 className="font-semibold mb-3 text-ieee-dark">Recent reviews</h2>
            {(!data.recent_reviews || data.recent_reviews.length === 0) ? (
              <p className="text-sm text-slate-500">No reviews yet. Create one to begin.</p>
            ) : (
              <div className="table-wrap">
                <table className="w-full">
                  <thead>
                    <tr><th className="th">Review ID</th><th className="th">Title</th><th className="th">Type</th><th className="th">Paper type</th><th className="th">Status</th></tr>
                  </thead>
                  <tbody>
                    {data.recent_reviews.map((r: any) => (
                      <tr key={r.review_id}>
                        <td className="td"><Link className="text-ieee hover:underline" href={`/reviews/${r.review_id}`}>{r.review_id}</Link></td>
                        <td className="td">{r.title}</td>
                        <td className="td">{r.submission_type}</td>
                        <td className="td">{r.paper_type}</td>
                        <td className="td"><span className="badge">{r.status}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
