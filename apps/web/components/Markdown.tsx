"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

/**
 * Renders review Markdown nicely. Engine outputs (claude/codex) often wrap the
 * whole review in a ```markdown fence — we unwrap those so they render as real
 * Markdown instead of a code block.
 */
function unwrap(md: string): string {
  if (!md) return "";
  let out = md;
  // Drop a leading ```markdown ... ``` wrapper (and stray fences around the doc).
  out = out.replace(/```markdown\s*/gi, "");
  // If after removing the opening fences there are dangling ``` lines that only
  // wrapped the doc, remove standalone fence lines.
  out = out.replace(/^\s*```\s*$/gm, "");
  // Internal placeholders are not something the user fills in by hand — show them
  // as a muted "pending" marker in the UI (the underlying data keeps the token).
  out = out.replace(/NEEDS_USER_INPUT\s*\([^)]*\)/g, "⏳ _pending — run a real engine_");
  out = out.replace(/\bNEEDS_USER_INPUT\b/g, "⏳ _pending_");
  return out;
}

export default function Markdown({ children }: { children: string }) {
  return (
    <div className="prose-jrs max-h-[34rem] overflow-auto rounded-md border border-slate-200 bg-white p-4 text-sm">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{unwrap(children || "(empty)")}</ReactMarkdown>
    </div>
  );
}
