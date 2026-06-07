# CLAUDE.md — journal-review-simulator

You are building a project called `journal-review-simulator`.

This project is a local web platform that simulates a scientific journal/conference submission and peer-review workflow. It must help the user evaluate manuscripts before real submission.

The system must behave like a pre-submission editorial simulator, not like a real peer-review system.

## Core architecture

Use this architectural rule:

* Markdown is the semantic memory.
* The database is only an index and workflow state manager.
* The web app is the user workflow.
* Agents are independent evaluators.
* Docker provides reproducible deployment.
* GitHub private repository is used for code, templates and configuration, not private papers by default.

## Main objective

Build a web-based system that allows the user to:

1. Create a review with a unique ID.
2. Upload a manuscript.
3. Accept PDF, DOCX, Markdown, LaTeX `.tex`, or ZIP containing LaTeX.
4. Mark the manuscript as new submission, resubmission, minor revision, major revision, reject-and-resubmit, or camera-ready.
5. Upload previous reviews and author response letters for resubmissions.
6. Extract the manuscript into Markdown.
7. Classify the paper by area and paper type.
8. Suggest suitable journals/conferences.
9. Configure venues manually or from CSV.
10. Store venue information as Markdown/YAML files.
11. Generate prompts for external AI engines: ChatGPT, Claude, Gemini, Perplexity and NotebookLM.
12. Allow the user to upload the external AI responses as Markdown, PDF or DOCX.
13. Run internal autonomous reviewers using subagents.
14. Allow reviewers to request additional information from the user.
15. Limit reviewer-user clarification iterations to a configurable maximum, default 3.
16. Generate an editor-in-chief decision.
17. Generate a revision plan.
18. Generate a rebuttal strategy.
19. Export the final review package.
20. Store full review history.

## Critical rules

* Never invent references.
* Never invent quartiles, rankings, impact factors, CiteScore, SJR, h-index, acceptance rates, publication times or review times.
* If information is missing, write `UNKNOWN`, `NOT_VERIFIED`, `MISSING`, or `NEEDS_USER_INPUT`.
* Separate evidence from the manuscript, reviewer inference, external verified data and missing information.
* If literature data is missing, novelty assessment must be marked as provisional.
* If venue data is incomplete, venue fit assessment must be marked as provisional.
* Do not download paywalled papers.
* Do not treat this as real peer review.
* Each reviewer must work independently.
* The editor-in-chief may synthesize reviewer outputs but must not mechanically average scores.
* Every output must be saved as Markdown, YAML, CSV or JSON.
* Every review must have a unique ID.
* Every uploaded file must be linked to a review ID.
* Every reviewer output must state:

  * review ID
  * venue ID
  * reviewer profile
  * engine/model used
  * data sources used
  * limitations
  * confidence

## Research areas

The system must support manuscripts related to:

### Cloud, systems and computer architecture

* computer architecture
* high-performance computing
* distributed systems
* cloud computing
* edge computing
* serverless computing
* Kubernetes
* orchestration
* CloudSim
* CloudSim Plus
* cloud task scheduling
* resource allocation
* load balancing
* priority scheduling
* starvation-free scheduling
* weighted fair queuing
* datacenter simulation
* energy-aware computing
* green computing
* hardware security
* RISC-V
* heterogeneous architectures
* computer architecture education
* digital sovereignty
* EU Chips Act

### Machine learning, computer vision and robust generalization

* machine learning
* deep learning
* computer vision
* transfer learning
* domain adaptation
* domain generalization
* out-of-distribution generalization
* covariate shift
* concept shift
* calibration transfer
* grouped cross-validation
* leakage-free evaluation
* benchmark design
* robust evaluation protocols
* model-free diagnostics
* interpretable machine learning
* explainable AI

### Face anti-spoofing, biometrics and security

* face anti-spoofing
* presentation attack detection
* biometric recognition
* biometric security
* face recognition security
* video-based identity verification
* spoofing detection
* replay attack detection
* print attack detection
* deepfake detection
* 3D convolutional neural networks
* spatiotemporal neural networks
* residual spatiotemporal networks
* lightweight FAS
* real-time FAS
* computational cost vs accuracy trade-off

### HTR, OCR and Document AI

* handwritten text recognition
* HTR
* OCR
* document analysis
* document image analysis
* document AI
* handwriting recognition
* offline handwriting recognition
* child handwriting recognition
* student handwriting recognition
* low-resource language HTR
* Catalan HTR
* multilingual HTR
* synthetic handwriting generation
* handwriting datasets
* writer-independent evaluation
* transformer-based HTR
* curriculum learning for HTR
* annotation protocols
* K–12 handwriting datasets

### Education and computing education

* educational technology
* computing education
* computer science education
* programming education
* introductory programming
* CS1 education
* K–12 computing education
* STEM education
* engineering education
* computational thinking
* natural language programming
* pseudocode-based programming
* block-based programming
* AI-supported programming education
* systematic literature reviews in education
* PRISMA systematic reviews
* curriculum analysis
* CS2023
* ACM/IEEE curriculum guidelines

### Agricultural AI, hyperspectral imaging and food safety

* agricultural AI
* precision agriculture
* wheat detection
* wheat quality assessment
* food safety
* food quality
* mycotoxin detection
* deoxynivalenol detection
* DON screening
* Fusarium detection
* near-infrared hyperspectral imaging
* NIR-HSI
* hyperspectral imaging
* spectroscopy
* chemometrics
* single-kernel grain analysis
* non-destructive testing
* calibration transfer
* spectral machine learning
* batch effect
* acquisition-session drift
* FAIR data
* reproducible agricultural benchmarks

### Dataset, benchmark and software papers

* data descriptor papers
* dataset papers
* benchmark papers
* corpus papers
* software papers
* reproducibility papers
* resource papers
* open science papers
* FAIR data papers
* benchmark protocol papers
* evaluation protocol papers

## Required stack

Create a modular system with:

* Frontend: Next.js or React.
* Backend API: FastAPI.
* Worker: Python.
* Database: PostgreSQL.
* Optional local models: Ollama.
* Deployment: Docker Compose.
* File-based knowledge: Markdown, YAML, CSV and JSON.

## Required project structure

Create this structure:

journal-review-simulator-web/
├── CLAUDE.md
├── README.md
├── docker-compose.yml
├── .env.example
├── .gitignore
├── apps/
│   ├── web/
│   └── api/
├── worker/
├── config/
├── db/
├── data/
│   ├── global_knowledge/
│   │   ├── venues/
│   │   ├── recent_papers/
│   │   ├── literature/
│   │   ├── reviewer_profiles/
│   │   └── prompt_templates/
│   ├── reviews/
│   └── uploads/
├── prompts/
├── .claude/
│   ├── agents/
│   └── skills/
├── scripts/
└── tests/

## Required web pages

Create a clean academic-style web interface with:

### Sidebar

* Dashboard
* Reviews
* New Review
* Papers
* Venues
* Recent Papers / SOTA
* External Prompts
* Pending Requests
* Reviewer Profiles
* AI Engines
* Settings
* Export / History

### Review wizard top menu

* 0. Create / Metadata
* 1. Upload
* 2. Extraction
* 3. Area & Paper Type
* 4. Venues
* 5. Desk-Reject Precheck
* 6. Reviewer Profiles
* 7. External Prompts
* 8. External Responses
* 9. Autonomous Review
* 10. Integrity Audit
* 11. Editor Decision
* 12. Revision Plan
* 13. Export

## Required review ID structure

Every review must have a unique ID like:

REV-YYYYMMDD-HHMMSS-XXXXXX

Example:

REV-20260607-143012-A8F3K2

Each review must create:

data/reviews/<review_id>/
├── metadata.yaml
├── input/
├── extracted/
├── venues/
├── literature/
├── external_prompts/
├── external_responses/
├── pending_requests/
├── reviewer_outputs/
├── editor/
├── exports/
└── audit/

## Upload requirements

Support:

* PDF
* DOCX
* Markdown
* LaTeX `.tex`
* ZIP with LaTeX
* BibTeX
* CSV
* YAML
* JSON

Implement safe upload validation:

* validate extension
* validate real MIME type
* limit file size
* rename files safely
* compute SHA256 hash
* store original file safely
* extract ZIP only in a sandbox
* block dangerous paths inside ZIP files
* block unexpected executables
* generate upload_report.md
* register file hashes

## Manuscript extraction

Priority order:

1. LaTeX
2. Markdown
3. DOCX
4. PDF

Extract:

* title
* abstract
* keywords
* research area
* problem statement
* claimed contributions
* methodology
* architecture/system design
* datasets
* experiments
* metrics
* baselines
* results summary
* limitations
* reproducibility artifacts
* ethical considerations
* references
* paper type
* likely venue families

Save:

data/reviews/<review_id>/extracted/manuscript_extracted.md
data/reviews/<review_id>/extracted/paper_extraction.md
data/reviews/<review_id>/extracted/paper_extraction.json

## Resubmission support

If the review is a resubmission, allow upload of:

* previous reviews
* editor letter
* response to reviewers
* previous manuscript
* new manuscript
* diff or list of changes

Generate:

data/reviews/<review_id>/input/resubmission_context.md
data/reviews/<review_id>/input/previous_reviews_summary.md
data/reviews/<review_id>/input/author_response_matrix.md
data/reviews/<review_id>/input/changes_claimed_by_authors.md

## Venue management

Allow users to:

* create a venue
* edit a venue
* import venues from CSV
* upload aims and scope
* upload author guidelines
* upload editorial policy
* upload review criteria
* upload format/template
* upload recent papers from the venue
* generate prompts for ChatGPT, Claude, Gemini, Perplexity and NotebookLM to complete missing venue information

Store each venue as Markdown/YAML:

data/global_knowledge/venues/journals/<venue_id>/
├── venue_profile.yaml
├── overview.md
├── aims_and_scope.md
├── author_guidelines.md
├── editorial_policy.md
├── review_criteria.md
├── indexing_and_quartile.md
├── publication_timeline.md
├── q1_accessibility.md
├── format_requirements.md
├── recent_papers/
├── example_papers/
└── verification_log.md

## External prompts

Generate prompts for:

* ChatGPT
* Claude
* Gemini
* Perplexity
* NotebookLM

Prompts must be generated per:

* review ID
* venue ID
* reviewer profile
* engine

Each prompt must specify:

* exact expected output filename
* target venue
* reviewer profile
* manuscript summary
* venue profile
* review criteria
* output format in Markdown
* instruction not to invent references or venue data
* instruction to separate evidence, inference, missing information and external knowledge

Expected filename format:

<review_id>*<venue_id>*<reviewer_profile>_<engine>_response.md

## Internal reviewers

Create these main reviewers:

1. reviewer-methodology
2. reviewer-domain
3. reviewer-systems-architecture
4. reviewer-reproducibility
5. reviewer-scientific-impact

Create these specialized reviewers:

* reviewer-document-ai-htr
* reviewer-education-research
* reviewer-dataset-benchmark
* reviewer-spectral-agri-food
* reviewer-fas-biometrics-security
* reviewer-cloud-hpc-scheduling
* format-compliance-checker
* integrity-ai-use-auditor

Reviewers must work independently.

Each reviewer must output:

* summary
* strengths
* major weaknesses
* minor weaknesses
* questions for authors
* scores
* recommendation
* confidence
* evidence table
* missing information
* required revisions

Allowed recommendations:

* accept
* minor revision
* major revision
* reject
* desk reject risk

## Pending requests

Agents may ask the user for additional information.

Default maximum: 3 iterations per agent.

Pending requests must be saved in:

data/reviews/<review_id>/pending_requests/pending_requests.md
data/reviews/<review_id>/pending_requests/pending_requests.json

## Integrity audit

Create an integrity auditor that checks:

* suspicious references
* unsupported claims
* inconsistencies between abstract, method, results and conclusions
* exaggerated contributions
* possible undeclared AI use
* data leakage
* plagiarism risk indicators
* dual-use concerns
* missing limitations
* missing reproducibility details
* author guideline compliance
* title/abstract coherence
* tone and clarity
* ethical issues
* privacy and consent if minors are involved
* dataset/code/license issues

## Editor-in-chief

The editor must read:

* manuscript extraction
* venue profile
* venue fit report
* publication timeline report
* five independent reviews
* specialized reviews
* external responses
* integrity audit
* literature matrix
* resubmission context, if available
* resolved pending requests

The editor must generate:

data/reviews/<review_id>/editor/editor_decision.md
data/reviews/<review_id>/editor/meta_review.md
data/reviews/<review_id>/editor/revision_plan.md
data/reviews/<review_id>/editor/rebuttal_strategy.md
data/reviews/<review_id>/editor/final_letter.md

Allowed final decisions:

* desk reject
* reject
* major revision
* minor revision
* accept

## Export

Export:

data/reviews/<review_id>/exports/
├── final_editor_decision.md
├── final_editor_decision.pdf
├── revision_plan.md
├── reviewer_response_matrix.md
├── rebuttal_letter_draft.md
├── venue_fit_report.md
├── audit_log.md
└── full_review_package.zip

## Docker

Create Docker Compose services:

* web
* api
* worker
* postgres
* ollama, optional
* local storage volume

Use persistent volumes for:

* postgres_data
* review_data
* upload_data
* ollama_data

## GitHub private repository

Prepare `.gitignore` so private or large files are not committed by default:

* data/reviews/
* data/uploads/
* PDFs
* ZIPs
* .env
* API keys
* local models
* temporary files

Version by default:

* code
* templates
* prompts
* generic reviewer profiles
* schemas
* configuration examples
* documentation

## Required scripts

Create:

* scripts/init_review.py
* scripts/run_pipeline.py
* scripts/parse_paper.py
* scripts/discover_venues.py
* scripts/scan_venue_markdowns.py
* scripts/build_literature_matrix.py
* scripts/compare_models.py
* scripts/build_report.py
* scripts/export_review_package.py

Main CLI:

python scripts/run_pipeline.py --review-id <review_id> --mode full_review

Supported modes:

* init
* validate_upload
* extract
* scan_venues
* discover_venues
* venue_fit
* timeline
* literature_queries
* generate_external_prompts
* import_external_responses
* review
* specialized_review
* integrity
* editorial_decision
* export
* full_review

## First implementation task

Build the first functional MVP.

Prioritize:

1. Folder structure.
2. Docker Compose.
3. Minimal FastAPI backend.
4. Minimal web UI with sidebar and review wizard.
5. Review ID creation.
6. Safe upload handling.
7. Basic extraction to Markdown.
8. Venue configuration.
9. External prompt generation.
10. External response import.
11. Markdown-based internal pipeline.
12. Reviewer profiles as `.md`.
13. Integrity audit.
14. Final export.
15. README.

After creating the files, run a basic structure check and explain:

* files created
* how to run with Docker Compose
* how to create a review
* how to upload a paper
* how to add venues
* how to generate external prompts
* how to upload external responses
* how to run the internal pipeline
* how to view history
* recommended next steps
