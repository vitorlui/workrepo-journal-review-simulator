Sí: lo diseñaría como un **simulador editorial multiagente**. La mejor arquitectura no es “un único prompt gigante que revise todo”, sino un proyecto en Claude Code con **carpetas, perfiles de revista, subagentes/revisores, literatura externa y salidas auditables**.

Asumo que “Cloud Code” = **Claude Code**. Claude Code puede leer y editar archivos, ejecutar comandos y trabajar sobre un proyecto completo desde terminal/IDE; además permite `CLAUDE.md`, skills, subagentes y ejecución no interactiva con `claude -p`. ([Claude API Docs][1]) ([Claude API Docs][2])
Para tu caso, conviene usar **Claude Code como orquestador principal** y usar Llama/Ollama solo como comparación secundaria. Claude Code también puede trabajar con skills mediante `SKILL.md`, que se cargan cuando son relevantes, y con subagentes especializados para aislar contexto entre tareas. ([Claude API Docs][3]) ([Claude API Docs][4])

---

## 1. Estructura recomendada del proyecto

```text
journal-review-simulator/
├── CLAUDE.md
├── README.md
├── config/
│   ├── pipeline.yaml
│   ├── scoring_rubrics.yaml
│   └── model_config.yaml
├── venues/
│   ├── template/
│   │   ├── venue_profile.yaml
│   │   ├── aims_and_scope.md
│   │   ├── author_guidelines.md
│   │   ├── editorial_policy.md
│   │   ├── review_criteria.md
│   │   └── example_papers/
│   ├── journal_x/
│   └── conference_y/
├── input/
│   └── papers/
│       └── paper_001/
│           ├── manuscript.pdf
│           ├── manuscript.md
│           ├── metadata.yaml
│           └── user_request.yaml
├── literature/
│   └── paper_001/
│       ├── perplexity_queries.md
│       ├── candidate_papers.bib
│       ├── literature_matrix.csv
│       └── notes/
├── reviewers/
│   ├── reviewer_1_methodology.md
│   ├── reviewer_2_domain_expert.md
│   ├── reviewer_3_reproducibility_ethics.md
│   └── editor.md
├── .claude/
│   ├── agents/
│   │   ├── editor-in-chief.md
│   │   ├── venue-fit-analyst.md
│   │   ├── literature-scout.md
│   │   ├── reviewer-methodology.md
│   │   ├── reviewer-domain.md
│   │   ├── reviewer-reproducibility.md
│   │   └── integrity-ai-use-reviewer.md
│   └── skills/
│       └── review-paper-reviewer/
│           └── SKILL.md
├── scripts/
│   ├── run_pipeline.py
│   ├── parse_paper.py
│   ├── compare_models.py
│   └── build_report.py
└── output/
    └── paper_001/
        ├── venue_fit_report.md
        ├── reviewer_1.md
        ├── reviewer_2.md
        ├── reviewer_3.md
        ├── editor_decision.md
        ├── meta_review.md
        ├── rebuttal_strategy.md
        ├── revision_plan.md
        └── audit_log.md
```

---

## 2. Qué debe hacer el pipeline

El flujo completo sería este:

**Fase 1 — Ingesta del paper**
El sistema lee el PDF o Markdown, extrae título, abstract, contribuciones, metodología, experimentos, datasets, resultados, limitaciones y referencias.

**Fase 2 — Selección o evaluación del venue**
Si indicas una revista concreta, el sistema evalúa el encaje. Si no indicas venue, compara el paper contra todos los perfiles de `venues/` y genera un ranking.

**Fase 3 — Generación de búsqueda externa**
El sistema no debe inventar artículos. Debe generar queries para Perplexity, Google Scholar, Semantic Scholar, Scopus o Web of Science. Tú puedes descargar o pegar los resultados legalmente disponibles. Después el sistema crea una matriz de literatura.

**Fase 4 — Simulación editorial**
Un editor decide si el paper pasa a revisión o si habría desk reject. Si pasa, asigna tres revisores con perfiles distintos.

**Fase 5 — Tres revisiones independientes**
Cada revisor produce una review sin ver las otras. Esto es importante para evitar convergencia artificial.

**Fase 6 — Integridad, IA y revisión ética**
Tu skill `review paper reviewer` entra al final para detectar problemas de uso de IA, trazabilidad, estructura, referencias sospechosas, claims no soportados y estilo.

**Fase 7 — Decisión editorial y plan de mejora**
El editor sintetiza las tres reviews, genera decisión, recomendaciones, plan de revisión y posible estrategia de rebuttal.

---

## 3. Perfil de cada revista

Cada revista debe tener un archivo como este:

```yaml
journal_id: "journal_x"
name: "Nombre de la revista"
publisher: "Editorial"
url: "https://..."
field: "Computer Science / Machine Learning / Distributed Computing"
article_types:
  - "Original research"
  - "Survey"
  - "Short communication"

aims_scope_summary: >
  Resumen corto del objetivo de la revista.

target_audience:
  - "Investigadores en..."
  - "Profesionales de..."

novelty_expectation: "high"
methodological_rigor: "high"
experimental_rigor: "high"
reproducibility_expectation: "medium"
theoretical_depth: "medium"
application_orientation: "high"

common_rejection_reasons:
  - "Fuera del scope"
  - "Contribución incremental"
  - "Evaluación experimental insuficiente"
  - "Estado del arte incompleto"
  - "Falta de claridad en la metodología"

review_dimensions:
  scope_fit: 0.20
  novelty: 0.20
  technical_quality: 0.20
  experimental_validation: 0.15
  clarity: 0.10
  reproducibility: 0.10
  ethics_and_integrity: 0.05

decision_thresholds:
  desk_reject_below: 55
  reject_below: 65
  major_revision_below: 78
  minor_revision_below: 88
  accept_from: 88
```

---

## 4. Los tres revisores que yo crearía

Para que el resultado sea útil, no haría tres revisores genéricos. Haría tres perfiles tensionados:

**Reviewer 1 — Metodología y validez interna**
Muy estricto. Busca fallos en hipótesis, diseño experimental, métricas, datasets, baselines, amenazas a la validez y claims exagerados.

**Reviewer 2 — Experto de dominio y estado del arte**
Evalúa si la contribución es realmente nueva frente a papers recientes. Este revisor depende mucho de la fase Perplexity/literatura.

**Reviewer 3 — Reproducibilidad, ética, escritura y uso de IA**
Evalúa claridad, estructura, disponibilidad de código/datos, reproducibilidad, sesgos, limitaciones, referencias sospechosas y señales de texto generado por IA.

Después, el **Editor-in-Chief** no debe simplemente promediar. Debe justificar una decisión editorial coherente.

---

## 5. Prompt completo para pegar en Claude Code

Aquí tienes el prompt principal para crear el sistema:

Quiero que construyas un proyecto local llamado `journal-review-simulator`.

Objetivo general:
Crear un sistema que simule el proceso editorial de una revista científica. El sistema debe aceptar un paper como entrada, evaluar su encaje con una revista concreta o sugerir venues adecuados, generar consultas de búsqueda de literatura actual, simular tres revisores independientes con perfiles distintos, aplicar una revisión final de integridad/uso de IA y producir una decisión editorial con plan de mejora.

Suposiciones:

* El sistema se ejecutará localmente desde terminal.
* La orquestación principal debe estar pensada para Claude Code.
* El diseño debe permitir comparar respuestas de Claude con respuestas de modelos locales tipo Llama/Ollama.
* El sistema no debe inventar referencias, métricas, papers, resultados ni políticas editoriales.
* Si falta información, debe marcarla como `UNKNOWN` o pedir que el usuario añada el archivo correspondiente.
* No debe descargar papers de pago ni contenido con copyright sin autorización. Debe limitarse a generar queries y usar únicamente documentos que el usuario aporte o fuentes legalmente accesibles.
* Todas las salidas deben ser auditables y guardarse en archivos Markdown, YAML, CSV o JSON.

Crea la siguiente estructura:

journal-review-simulator/
├── CLAUDE.md
├── README.md
├── config/
│   ├── pipeline.yaml
│   ├── scoring_rubrics.yaml
│   └── model_config.yaml
├── venues/
│   ├── template/
│   │   ├── venue_profile.yaml
│   │   ├── aims_and_scope.md
│   │   ├── author_guidelines.md
│   │   ├── editorial_policy.md
│   │   ├── review_criteria.md
│   │   └── example_papers/
├── input/
│   └── papers/
│       └── paper_001/
│           ├── manuscript.pdf
│           ├── manuscript.md
│           ├── metadata.yaml
│           └── user_request.yaml
├── literature/
│   └── paper_001/
│       ├── perplexity_queries.md
│       ├── candidate_papers.bib
│       ├── literature_matrix.csv
│       └── notes/
├── reviewers/
│   ├── reviewer_1_methodology.md
│   ├── reviewer_2_domain_expert.md
│   ├── reviewer_3_reproducibility_ethics.md
│   └── editor.md
├── .claude/
│   ├── agents/
│   │   ├── editor-in-chief.md
│   │   ├── venue-fit-analyst.md
│   │   ├── literature-scout.md
│   │   ├── reviewer-methodology.md
│   │   ├── reviewer-domain.md
│   │   ├── reviewer-reproducibility.md
│   │   └── integrity-ai-use-reviewer.md
│   └── skills/
│       └── review-paper-reviewer/
│           └── SKILL.md
├── scripts/
│   ├── run_pipeline.py
│   ├── parse_paper.py
│   ├── compare_models.py
│   └── build_report.py
└── output/

Implementa el sistema con las siguientes fases:

1. Ingesta del paper

* Leer `input/papers/<paper_id>/manuscript.md` si existe.
* Si solo existe PDF, crear un placeholder en `parse_paper.py` para extracción posterior.
* Extraer o pedir estos campos:

  * title
  * abstract
  * keywords
  * research_area
  * claimed_contributions
  * methodology
  * datasets
  * experiments
  * metrics
  * baselines
  * results_summary
  * limitations
  * references

2. Evaluación de venue

* Si `user_request.yaml` contiene `target_venue`, evaluar ese venue.
* Si no contiene `target_venue`, comparar contra todos los venues disponibles en `venues/`.
* Generar `output/<paper_id>/venue_fit_report.md`.
* Incluir:

  * ranking de venues
  * score de encaje
  * razones a favor
  * riesgos de desk reject
  * cambios necesarios antes de enviar
  * campos faltantes en el perfil del venue

3. Generación de queries para literatura

* Crear `literature/<paper_id>/perplexity_queries.md`.
* Generar queries separadas para:

  * papers más recientes de los últimos 2 años
  * papers fundacionales
  * surveys/reviews
  * datasets y benchmarks
  * métodos competidores
  * críticas o limitaciones del enfoque
* Las queries deben ser específicas al título, abstract, keywords y contribuciones del paper.
* No inventar resultados. Solo crear queries y plantilla para que el usuario pegue resultados reales.

4. Matriz de literatura

* Crear una plantilla `literature/<paper_id>/literature_matrix.csv` con columnas:

  * citation_key
  * title
  * year
  * venue
  * authors
  * problem
  * method
  * dataset
  * metrics
  * key_result
  * relation_to_current_paper
  * difference_from_current_paper
  * supports_claim
  * challenges_claim
  * notes

5. Revisor 1: metodología

* Crear un subagente `reviewer-methodology`.
* Perfil:

  * Muy estricto.
  * Prioriza validez interna, diseño experimental, baselines, métricas, amenazas a la validez y claims no soportados.
  * No debe evaluar estilo salvo que afecte la comprensión científica.
* Salida:

  * resumen del paper
  * fortalezas
  * debilidades mayores
  * debilidades menores
  * preguntas para autores
  * score por dimensión
  * recomendación: accept, minor revision, major revision, reject
  * confianza de la recomendación
  * evidencias textuales del paper

6. Revisor 2: experto de dominio

* Crear un subagente `reviewer-domain`.
* Perfil:

  * Experto en el área específica del paper.
  * Evalúa novedad, actualidad del estado del arte, relación con trabajos recientes y relevancia para la comunidad.
  * Debe usar la matriz de literatura si existe.
  * Si la matriz está vacía, debe declarar que la evaluación de novedad es provisional.
* Salida igual al Revisor 1, pero centrada en novedad y posicionamiento científico.

7. Revisor 3: reproducibilidad, ética y escritura

* Crear un subagente `reviewer-reproducibility`.
* Perfil:

  * Evalúa claridad, estructura, reproducibilidad, disponibilidad de código/datos, descripción de hiperparámetros, ética, sesgos, limitaciones, formato y señales de texto generado por IA.
  * Debe distinguir entre problemas científicos graves y problemas de presentación.
* Salida igual al Revisor 1, pero centrada en reproducibilidad, ética e integridad.

8. Revisión final de integridad/IA

* Crear o integrar la skill `review-paper-reviewer`.
* Esta fase debe revisar:

  * referencias sospechosas o incompletas
  * afirmaciones sin evidencia
  * uso de IA no declarado si parece relevante
  * inconsistencias entre abstract, método y resultados
  * problemas de estilo académico
  * posible exageración de contribuciones
  * cumplimiento básico de la guía de autores del venue
* Guardar salida en `output/<paper_id>/integrity_ai_review.md`.

9. Decisión editorial

* Crear un subagente `editor-in-chief`.
* Debe leer:

  * venue profile
  * venue fit report
  * reviewer_1.md
  * reviewer_2.md
  * reviewer_3.md
  * integrity_ai_review.md
* Debe producir:

  * `editor_decision.md`
  * `meta_review.md`
  * `revision_plan.md`
  * `rebuttal_strategy.md`
* La decisión debe ser una de:

  * desk reject
  * reject
  * major revision
  * minor revision
  * accept
* La decisión debe justificar discrepancias entre revisores.
* No debe hacer promedio mecánico.
* Debe incluir una sección “Qué tendría que cambiar para que este paper sea aceptable”.

10. Comparación con Llama/Ollama

* Crear `scripts/compare_models.py`.
* Debe permitir guardar respuestas alternativas de otros modelos usando el mismo prompt base.
* No hace falta implementar conexión real completa si no hay credenciales o servidor local, pero debe dejar una interfaz clara:

  * provider: claude
  * provider: ollama
  * model: configurable
  * input_prompt
  * output_file
* Las comparaciones deben guardarse en:

  * `output/<paper_id>/model_comparison/`

11. Auditoría

* Crear `output/<paper_id>/audit_log.md`.
* Registrar:

  * fecha de ejecución
  * paper_id
  * target_venue
  * archivos leídos
  * archivos generados
  * literatura disponible o ausente
  * limitaciones de la evaluación
  * advertencias sobre información faltante

Crea también:

* `README.md` con instrucciones de uso.
* `CLAUDE.md` con reglas del proyecto.
* Plantillas de venue.
* Plantillas de reviewer.
* Un ejemplo mínimo de `user_request.yaml`.
* Un ejemplo mínimo de `pipeline.yaml`.

Reglas críticas:

* Nunca inventes referencias bibliográficas.
* Nunca afirmes que un paper es “actual” si no hay literatura real aportada.
* Nunca confundas revisión editorial simulada con revisión real por pares.
* Siempre separa claramente:

  * evidencia extraída del paper
  * inferencia del revisor
  * información faltante
  * recomendación editorial
* Cada revisor debe actuar de forma independiente.
* El editor puede sintetizar, pero no debe borrar desacuerdos.
* Las salidas deben ser útiles para mejorar el paper antes de enviarlo a una revista real.

Después de crear los archivos, explícame:

1. Cómo ejecutar el pipeline.
2. Cómo añadir una nueva revista.
3. Cómo añadir un nuevo paper.
4. Cómo usar Perplexity dentro del flujo.
5. Cómo comparar Claude con Llama/Ollama.
6. Qué partes son automáticas y qué partes requieren intervención humana.

---

## 6. Prompt corto para ejecutar una revisión concreta

Cuando el sistema ya exista, usaría un prompt operativo así:

```text
Ejecuta el pipeline editorial para `paper_001`.

Parámetros:
- target_venue: journal_x
- mode: full_review
- reviewers: 3
- include_venue_fit: true
- include_literature_queries: true
- include_integrity_ai_review: true
- generate_rebuttal_strategy: true
- generate_revision_plan: true

Reglas:
- No inventes referencias.
- Si la matriz de literatura está vacía, declara que la evaluación de novedad es provisional.
- Guarda todas las salidas en `output/paper_001/`.
- Los tres revisores deben trabajar de forma independiente.
- El editor debe justificar la decisión final sin hacer un simple promedio.
```

---

## 7. Cómo integraría Perplexity

No intentaría que Claude Code “descargue todo” automáticamente. Haría esto:

1. El sistema genera `perplexity_queries.md`.
2. Tú copias esas queries en Perplexity.
3. Pegas los resultados relevantes en `literature/paper_001/notes/`.
4. Añades BibTeX o metadata en `candidate_papers.bib`.
5. El sistema construye `literature_matrix.csv`.
6. El Revisor 2 usa esa matriz para evaluar novedad y estado del arte.

Esto evita el problema típico de revisores artificiales: **parecen convincentes, pero inventan el estado del arte**.

---

## 8. Cómo compararía Claude con Llama

Yo haría la comparación a nivel de **misma entrada, mismo rol, misma rúbrica**:

```text
model_comparison/
├── reviewer_1_claude.md
├── reviewer_1_llama.md
├── reviewer_2_claude.md
├── reviewer_2_llama.md
├── reviewer_3_claude.md
├── reviewer_3_llama.md
└── comparison_report.md
```

Claude sería el modelo principal para las reviews más exigentes. Llama/Ollama lo usaría como baseline local para ver diferencias de severidad, omisiones, alucinaciones y consistencia. Para conectarlo, puedes usar Ollama o LiteLLM; LiteLLM documenta soporte para Ollama, y Ollama ofrece compatibilidad con APIs estilo OpenAI, lo que facilita reutilizar el mismo adaptador de modelos. ([LiteLLM][5]) ([Ollama][6])

---

## 9. Recomendación práctica

Empieza con una versión mínima:

1. `venues/template/`
2. `input/papers/paper_001/manuscript.md`
3. `CLAUDE.md`
4. Tres subagentes revisores
5. Un editor
6. Salidas Markdown

Después añades automatización con Python, Perplexity, BibTeX, matriz de literatura y comparación Claude/Llama.

La clave para que funcione bien es que cada revista tenga buenos datos: **aims & scope, author guidelines, editorial policy, criterios de revisión y ejemplos de papers aceptados**. Sin eso, el sistema puede revisar el paper, pero no puede simular fielmente una revista concreta.

[1]: https://docs.anthropic.com/en/docs/claude-code/overview "Overview - Claude Code Docs"
[2]: https://docs.anthropic.com/en/docs/claude-code/cli-reference "CLI reference - Claude Code Docs"
[3]: https://docs.anthropic.com/en/docs/claude-code/slash-commands "Extend Claude with skills - Claude Code Docs"
[4]: https://docs.anthropic.com/en/docs/claude-code/sub-agents?utm_source=chatgpt.com "Create custom subagents - Claude Code Docs"
[5]: https://docs.litellm.ai/docs/providers/ollama?utm_source=chatgpt.com "Ollama"
[6]: https://docs.ollama.com/api/openai-compatibility?utm_source=chatgpt.com "OpenAI compatibility"
