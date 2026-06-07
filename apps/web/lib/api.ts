// Minimal API client for the FastAPI backend.
export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function jfetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  base: API_BASE,
  health: () => jfetch<any>("/health"),
  dashboard: () => jfetch<any>("/dashboard"),

  listReviews: () => jfetch<any[]>("/reviews"),
  getReview: (id: string) => jfetch<any>(`/reviews/${id}`),
  createReview: (title: string, submission_type: string) =>
    jfetch<any>("/reviews", { method: "POST", body: JSON.stringify({ title, submission_type }) }),
  getExtraction: (id: string) => jfetch<any>(`/reviews/${id}/extracted`),
  selectVenues: (id: string, venue_ids: string[]) =>
    jfetch<any>(`/reviews/${id}/select-venues`, { method: "POST", body: JSON.stringify({ venue_ids }) }),
  tree: (id: string) => jfetch<any>(`/reviews/${id}/tree`),
  artifact: (id: string, relpath: string) =>
    jfetch<any>(`/reviews/${id}/artifact?relpath=${encodeURIComponent(relpath)}`),
  externalPrompts: (id: string) => jfetch<any>(`/reviews/${id}/external-prompts`),
  externalResponses: (id: string) => jfetch<any>(`/reviews/${id}/external-responses`),
  pending: (id: string) => jfetch<any>(`/reviews/${id}/pending-requests`),

  runPipeline: (id: string, mode: string) =>
    jfetch<any>(`/pipeline/${id}/run?mode=${encodeURIComponent(mode)}`, { method: "POST" }),
  modes: () => jfetch<any>("/pipeline/modes"),

  listVenues: () => jfetch<any[]>("/venues"),
  getVenue: (vid: string) => jfetch<any>(`/venues/${vid}`),
  createVenue: (body: any) => jfetch<any>("/venues", { method: "POST", body: JSON.stringify(body) }),

  reviewerProfiles: () => jfetch<any>("/reviewer-profiles"),
  aiEngines: () => jfetch<any>("/ai-engines"),
  engineStatus: () => jfetch<any>("/engine-status"),
  runQuery: (id: string, body: { venue_id: string; reviewer_profile: string; engine: string }) =>
    jfetch<any>(`/reviews/${id}/run-query`, { method: "POST", body: JSON.stringify(body) }),
  vdReports: () => jfetch<any>("/venue-discovery/reports"),
  vdReport: (name: string) => jfetch<any>(`/venue-discovery/reports/${encodeURIComponent(name)}`),
  vdImportRawDir: () => jfetch<any>("/venue-discovery/import-raw-dir", { method: "POST" }),
};

// multipart helpers (no JSON content-type)
export async function uploadFile(path: string, file: File, extra?: Record<string, string>) {
  const fd = new FormData();
  fd.append("file", file);
  if (extra) for (const [k, v] of Object.entries(extra)) fd.append(k, v);
  const res = await fetch(`${API_BASE}${path}`, { method: "POST", body: fd });
  if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
  return res.json();
}
