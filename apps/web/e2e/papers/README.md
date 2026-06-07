# Drop your papers here

`paper-runs.spec.ts` creates one E2E test per file in this folder: create review →
upload → extract → classify → open venues.

- Accepted: `.pdf .docx .md .markdown .tex .zip`.
- Your private papers are **git-ignored** here (only `sample_manuscript.md` and this README
  are versioned), so dropping real manuscripts won't commit them.

Watch it run slowly, paper by paper:

```powershell
# stack must be up (web :3000 + api :8000)
cd apps\web
$env:PW_SLOWMO = "800"
npm run test:e2e:headed -- paper-runs.spec.ts
```
