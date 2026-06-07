export default function PendingRequestsPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-ieee-dark">Pending Requests</h1>
      <div className="card text-sm text-slate-600 space-y-2">
        <p>Reviewers may request additional information from you (missing venue data, SOTA, author guidelines,
          dataset details, resubmission context, clarifications, ...).</p>
        <p>Each agent may ask up to a configurable maximum (default <strong>3</strong> iterations, set in
          <code className="mx-1">config/pipeline.yaml</code>). Open pending requests appear on the relevant review and
          are stored in <code>data/reviews/&lt;review_id&gt;/pending_requests/</code>.</p>
        <p className="text-xs text-slate-400">In this first version the offline pipeline does not auto-raise requests; the structure and per-review API are in place for when live reviewers are enabled.</p>
      </div>
    </div>
  );
}
