"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

type Step = {
  title: string;
  body: string;
  action?: { label: string; href: string };
};

const STEPS: Step[] = [
  {
    title: "Welcome 👋",
    body:
      "This is a pre-submission editorial simulator — it helps you pre-evaluate a manuscript before " +
      "you submit to a real journal/conference. It is NOT real peer review. Markdown/YAML files are the " +
      "memory; the database is just an index. This quick tour walks you through your first run.",
  },
  {
    title: "1 · Create a review",
    body:
      "Start in “New Review”. Give it a working title and a submission type (new submission, " +
      "resubmission, revision…). You get a unique review ID and a documental folder for everything.",
    action: { label: "Go to New Review", href: "/reviews/new" },
  },
  {
    title: "2 · Upload your paper",
    body:
      "Open the review → step “1. Upload”. Accepted: PDF, DOCX, Markdown, LaTeX .tex, or a ZIP with " +
      "LaTeX (+figures+BibTeX). Files are validated (type, size, safe ZIP paths). For resubmissions you " +
      "can also upload previous reviews and the author response.",
  },
  {
    title: "3 · Extract & classify",
    body:
      "Steps “2. Extraction” and “3. Area & Paper Type”. The system extracts the manuscript to Markdown " +
      "(priority LaTeX > MD > DOCX > PDF) and detects research areas + paper type by keywords. Anything it " +
      "can’t find is marked NEEDS_USER_INPUT — never invented.",
  },
  {
    title: "4 · Choose venues",
    body:
      "Step “4. Venues”. 37 venues are already imported from the Perplexity research. Tick the ones you " +
      "want to target and Save. You can also import more (Venues page → Import venue discovery) or add one " +
      "manually. Quartiles/timelines are shown verbatim — unverified stays “not verified”.",
    action: { label: "Open Venues", href: "/venues" },
  },
  {
    title: "5 · External prompts & Execute query",
    body:
      "Step “7. External Prompts”. Generate per venue×reviewer×engine prompts to copy into an LLM, OR use " +
      "“Execute query”: pick venue + reviewer + engine and a worker runs the engine CLI (Claude / Codex / " +
      "Ollama / Gemini) and saves the response automatically. Greyed-out engines aren’t installed.",
  },
  {
    title: "6 · Autonomous review + integrity",
    body:
      "Step “9. Autonomous Review” runs 5 main reviewers + the specialized ones (auto-activated by area). " +
      "Step “10. Integrity Audit” checks references, claims, ethics, AI-use, licenses… Each runs " +
      "independently and reports sources, limitations and confidence.",
  },
  {
    title: "7 · Editor decision & export",
    body:
      "Step “11. Editor Decision” synthesizes the reviews (without averaging) into a decision + revision " +
      "plan + rebuttal strategy. Step “13. Export” bundles everything into a zip (PDF best-effort). " +
      "Tip: the “Run full review” button at the top runs steps 2→13 in one go.",
  },
  {
    title: "8 · Use real engines (optional)",
    body:
      "By default reviewers produce offline scaffolds. To get real content, run the backend natively on " +
      "your computer and set PIPELINE_ENGINE=claude|codex|gemini|ollama (each CLI needs a one-time login; " +
      "no extra cost beyond your plans). See the README “Host setup” section. You’re ready — good luck!",
  },
];

const SEEN_KEY = "jrs_help_seen_v1";

export default function HelpButton() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [i, setI] = useState(0);

  // Auto-open once on first ever visit.
  useEffect(() => {
    try {
      if (!localStorage.getItem(SEEN_KEY)) {
        setOpen(true);
        setI(0);
      }
    } catch {
      /* ignore */
    }
  }, []);

  // Esc to close.
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") close();
      if (e.key === "ArrowRight") setI((x) => Math.min(x + 1, STEPS.length - 1));
      if (e.key === "ArrowLeft") setI((x) => Math.max(x - 1, 0));
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  function markSeen() {
    try { localStorage.setItem(SEEN_KEY, "1"); } catch { /* ignore */ }
  }
  function close() { setOpen(false); markSeen(); }
  function openTour() { setI(0); setOpen(true); }

  const step = STEPS[i];
  const last = i === STEPS.length - 1;

  return (
    <>
      <button
        aria-label="Help — guided tour"
        title="Help"
        onClick={openTour}
        className="fixed bottom-6 right-6 z-40 h-12 w-12 rounded-full bg-ieee text-white text-2xl font-semibold shadow-lg hover:bg-ieee-dark focus:outline-none focus:ring-4 focus:ring-ieee/30"
      >
        ?
      </button>

      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" role="dialog" aria-modal="true">
          <div className="absolute inset-0 bg-black/40" onClick={close} />
          <div className="relative z-10 w-full max-w-lg rounded-xl bg-white shadow-xl border border-slate-200">
            <div className="flex items-center justify-between px-5 py-3 border-b border-slate-200">
              <div className="text-xs font-medium text-slate-400">
                Guided tour · {i + 1}/{STEPS.length}
              </div>
              <button aria-label="Close" onClick={close} className="text-slate-400 hover:text-slate-700 text-xl leading-none">×</button>
            </div>

            <div className="px-5 py-5">
              <h2 className="text-lg font-semibold text-ieee-dark">{step.title}</h2>
              <p className="mt-2 text-sm leading-relaxed text-slate-600">{step.body}</p>
              {step.action && (
                <button
                  onClick={() => { close(); router.push(step.action!.href); }}
                  className="btn-primary mt-4"
                >
                  {step.action.label} →
                </button>
              )}
            </div>

            {/* progress dots */}
            <div className="flex justify-center gap-1.5 pb-3">
              {STEPS.map((_, idx) => (
                <span key={idx} className={`h-1.5 rounded-full transition-all ${idx === i ? "w-5 bg-ieee" : "w-1.5 bg-slate-300"}`} />
              ))}
            </div>

            <div className="flex items-center justify-between px-5 py-3 border-t border-slate-200">
              <button className="btn-ghost" onClick={() => setI((x) => Math.max(x - 1, 0))} disabled={i === 0}>Back</button>
              <button className="text-xs text-slate-400 hover:text-slate-600" onClick={close}>Skip</button>
              {last ? (
                <button className="btn-primary" onClick={close}>Done</button>
              ) : (
                <button className="btn-primary" onClick={() => setI((x) => Math.min(x + 1, STEPS.length - 1))}>Next</button>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
