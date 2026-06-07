export default function ExternalPromptsPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-ieee-dark">External Prompts</h1>
      <div className="card text-sm text-slate-600 space-y-2">
        <p>External prompts are generated <strong>per review</strong>, for each selected venue × reviewer × engine
          (ChatGPT, Claude, Gemini, Perplexity, NotebookLM).</p>
        <p>Open a review and go to step <strong>7. External Prompts</strong> to generate them, then copy each prompt
          into the external engine and upload the response in step <strong>8. External Responses</strong>.</p>
        <p className="text-xs text-slate-400">Each prompt declares the exact expected response filename so imports auto-detect engine, reviewer and venue.</p>
      </div>
    </div>
  );
}
