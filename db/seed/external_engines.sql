-- Seed external AI engines (manual prompt/response workflow).
-- Idempotent: safe to run multiple times.
INSERT INTO external_engines (engine_id, name, mode) VALUES
  ('chatgpt',    'ChatGPT',    'manual_external_prompt'),
  ('claude',     'Claude',     'manual_external_prompt'),
  ('gemini',     'Gemini',     'manual_external_prompt'),
  ('perplexity', 'Perplexity', 'manual_external_prompt'),
  ('notebooklm', 'NotebookLM', 'manual_external_prompt')
ON CONFLICT (engine_id) DO NOTHING;
