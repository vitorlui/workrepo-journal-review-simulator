-- Seed reviewer-profile registry rows. The canonical rubric text lives in
-- data/global_knowledge/reviewer_profiles/<id>.md (plan C8); this only indexes them.
-- Idempotent.
INSERT INTO reviewer_profiles (profile_id, title, kind, path_on_disk) VALUES
  ('reviewer-methodology',           'Reviewer 1 — Methodology & experimental validity', 'main',        'data/global_knowledge/reviewer_profiles/reviewer-methodology.md'),
  ('reviewer-domain',                'Reviewer 2 — Domain expert & state of the art',     'main',        'data/global_knowledge/reviewer_profiles/reviewer-domain.md'),
  ('reviewer-systems-architecture',  'Reviewer 3 — Systems, architecture & implementation','main',       'data/global_knowledge/reviewer_profiles/reviewer-systems-architecture.md'),
  ('reviewer-reproducibility',       'Reviewer 4 — Reproducibility & empirical robustness','main',       'data/global_knowledge/reviewer_profiles/reviewer-reproducibility.md'),
  ('reviewer-scientific-impact',     'Reviewer 5 — Scientific impact & editorial strategy','main',       'data/global_knowledge/reviewer_profiles/reviewer-scientific-impact.md'),
  ('reviewer-document-ai-htr',       'Specialized — Document AI / HTR / OCR',             'specialized', 'data/global_knowledge/reviewer_profiles/reviewer-document-ai-htr.md'),
  ('reviewer-education-research',    'Specialized — Education research',                  'specialized', 'data/global_knowledge/reviewer_profiles/reviewer-education-research.md'),
  ('reviewer-dataset-benchmark',     'Specialized — Dataset / benchmark / data descriptor','specialized','data/global_knowledge/reviewer_profiles/reviewer-dataset-benchmark.md'),
  ('reviewer-spectral-agri-food',    'Specialized — Spectral / agri / food safety',       'specialized', 'data/global_knowledge/reviewer_profiles/reviewer-spectral-agri-food.md'),
  ('reviewer-fas-biometrics-security','Specialized — FAS / biometrics / security',        'specialized', 'data/global_knowledge/reviewer_profiles/reviewer-fas-biometrics-security.md'),
  ('reviewer-cloud-hpc-scheduling',  'Specialized — Cloud / HPC / scheduling',            'specialized', 'data/global_knowledge/reviewer_profiles/reviewer-cloud-hpc-scheduling.md'),
  ('format-compliance-checker',      'Format compliance checker',                         'auditor',     'data/global_knowledge/reviewer_profiles/format-compliance-checker.md'),
  ('integrity-ai-use-auditor',       'Integrity / AI-use auditor',                        'auditor',     'data/global_knowledge/reviewer_profiles/integrity-ai-use-auditor.md')
ON CONFLICT (profile_id) DO NOTHING;
