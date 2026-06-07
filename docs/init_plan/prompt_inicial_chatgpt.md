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
