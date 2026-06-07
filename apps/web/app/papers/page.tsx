"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

export default function PapersPage() {
  const [rows, setRows] = useState<any[]>([]);
  useEffect(() => { api.listReviews().then(setRows).catch(() => {}); }, []);
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-ieee-dark">Papers</h1>
      <p className="text-sm text-slate-600">Manuscripts under review, indexed by their review. Open a review to upload or re-extract its paper.</p>
      <div className="table-wrap">
        <table className="w-full">
          <thead><tr><th className="th">Review</th><th className="th">Title</th><th className="th">Paper type</th><th className="th">Areas</th></tr></thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.review_id}>
                <td className="td"><Link className="text-ieee hover:underline" href={`/reviews/${r.review_id}`}>{r.review_id}</Link></td>
                <td className="td">{r.title}</td>
                <td className="td">{r.paper_type}</td>
                <td className="td text-xs">{Array.isArray(r.detected_areas) ? r.detected_areas.join(", ") : ""}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
