export default function RecentPapersPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-ieee-dark">Recent Papers / SOTA</h1>
      <div className="card text-sm text-slate-600 space-y-2">
        <p>The knowledge base stores recent/state-of-the-art papers per area under
          <code className="mx-1">data/global_knowledge/recent_papers/&lt;paper_id&gt;/</code>.</p>
        <p>Each entry holds <code>paper_profile.yaml</code>, <code>extracted_summary.md</code>,
          relevance-by-area / reviewer / venue notes, and a citation. These feed the domain
          reviewer&apos;s novelty assessment (which stays provisional until real literature is added).</p>
        <p className="text-xs text-slate-400">Upload/extraction UI for recent papers is a planned next step; for now add files directly to the knowledge base folder.</p>
      </div>
    </div>
  );
}
