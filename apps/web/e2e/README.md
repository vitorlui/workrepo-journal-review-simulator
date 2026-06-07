# E2E tests (Playwright)

These drive the real web UI in a browser. They assume the stack is already
running (web on :3000, API on :8000).

```bash
# 1) start the stack (either)
docker compose up           # web:3000 + api:8000
#   or, native:  (api)  uvicorn app.main:app --app-dir apps/api --port 8000
#                (web)  npm run dev

# 2) one-time browser install
cd apps/web
npm install
npm run test:e2e:install

# 3) run
npm run test:e2e
# point at another host:  E2E_BASE_URL=http://localhost:3000 npm run test:e2e
```

Specs:
- `smoke.spec.ts` — dashboard, sidebar, venues table, reviewer profiles, AI engines.
- `review-flow.spec.ts` — create a review, open the 13-step wizard, and verify the
  External-Prompts **Execute query** controls render.
