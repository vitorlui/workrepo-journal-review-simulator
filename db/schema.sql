-- Generated reference snapshot of the SQLAlchemy models in worker/db.py (plan C9).
-- The ORM models are canonical; regenerate with scripts/dump_schema.py.
-- The DB is an INDEX + workflow-state manager only; Markdown/YAML is the source of truth.


CREATE TABLE IF NOT EXISTS audit_events (
	id SERIAL NOT NULL, 
	review_id VARCHAR(64) NOT NULL, 
	event_type VARCHAR(64) NOT NULL, 
	message TEXT NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS editorial_decisions (
	id SERIAL NOT NULL, 
	review_id VARCHAR(64) NOT NULL, 
	venue_id VARCHAR(128) NOT NULL, 
	decision VARCHAR(64) NOT NULL, 
	decision_path TEXT NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS external_engines (
	id SERIAL NOT NULL, 
	engine_id VARCHAR(64) NOT NULL, 
	name VARCHAR(128) NOT NULL, 
	mode VARCHAR(64) NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS external_prompts (
	id SERIAL NOT NULL, 
	review_id VARCHAR(64) NOT NULL, 
	venue_id VARCHAR(128) NOT NULL, 
	reviewer_profile VARCHAR(128) NOT NULL, 
	engine VARCHAR(64) NOT NULL, 
	prompt_file_path TEXT NOT NULL, 
	expected_response_filename TEXT NOT NULL, 
	status VARCHAR(32) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS external_responses (
	id SERIAL NOT NULL, 
	review_id VARCHAR(64) NOT NULL, 
	venue_id VARCHAR(128) NOT NULL, 
	reviewer_profile VARCHAR(128) NOT NULL, 
	engine VARCHAR(64) NOT NULL, 
	response_file_path TEXT NOT NULL, 
	has_sources BOOLEAN NOT NULL, 
	looks_incomplete BOOLEAN NOT NULL, 
	status VARCHAR(32) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS extracted_documents (
	id SERIAL NOT NULL, 
	review_id VARCHAR(64) NOT NULL, 
	kind VARCHAR(64) NOT NULL, 
	path_on_disk TEXT NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS internal_agent_runs (
	id SERIAL NOT NULL, 
	review_id VARCHAR(64) NOT NULL, 
	venue_id VARCHAR(128) NOT NULL, 
	agent_id VARCHAR(128) NOT NULL, 
	reviewer_profile VARCHAR(128) NOT NULL, 
	engine VARCHAR(64) NOT NULL, 
	model VARCHAR(128) NOT NULL, 
	mode VARCHAR(64) NOT NULL, 
	output_path TEXT NOT NULL, 
	status VARCHAR(32) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS literature_items (
	id SERIAL NOT NULL, 
	review_id VARCHAR(64) NOT NULL, 
	citation_key VARCHAR(256) NOT NULL, 
	title TEXT NOT NULL, 
	year VARCHAR(16) NOT NULL, 
	venue VARCHAR(256) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS papers (
	id SERIAL NOT NULL, 
	review_id VARCHAR(64) NOT NULL, 
	title VARCHAR(512) NOT NULL, 
	abstract TEXT NOT NULL, 
	paper_type VARCHAR(128) NOT NULL, 
	detected_areas TEXT NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS pending_requests (
	id SERIAL NOT NULL, 
	pending_id VARCHAR(64) NOT NULL, 
	review_id VARCHAR(64) NOT NULL, 
	venue_id VARCHAR(128) NOT NULL, 
	agent_id VARCHAR(128) NOT NULL, 
	reviewer_profile VARCHAR(128) NOT NULL, 
	request_type VARCHAR(64) NOT NULL, 
	question TEXT NOT NULL, 
	suggested_engine VARCHAR(64) NOT NULL, 
	generated_prompt_path TEXT NOT NULL, 
	status VARCHAR(32) NOT NULL, 
	iteration_number INTEGER NOT NULL, 
	max_iterations INTEGER NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS recent_papers (
	id SERIAL NOT NULL, 
	paper_id VARCHAR(128) NOT NULL, 
	title TEXT NOT NULL, 
	area VARCHAR(256) NOT NULL, 
	marker VARCHAR(64) NOT NULL, 
	path_on_disk TEXT NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS reviewer_profiles (
	id SERIAL NOT NULL, 
	profile_id VARCHAR(128) NOT NULL, 
	title VARCHAR(256) NOT NULL, 
	kind VARCHAR(32) NOT NULL, 
	path_on_disk TEXT NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS reviews (
	id SERIAL NOT NULL, 
	review_id VARCHAR(64) NOT NULL, 
	title VARCHAR(512) NOT NULL, 
	status VARCHAR(64) NOT NULL, 
	submission_type VARCHAR(64) NOT NULL, 
	selected_venue_id VARCHAR(128), 
	paper_type VARCHAR(128) NOT NULL, 
	detected_areas TEXT NOT NULL, 
	current_step INTEGER NOT NULL, 
	final_decision VARCHAR(64), 
	path_on_disk TEXT NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS uploaded_files (
	id SERIAL NOT NULL, 
	review_id VARCHAR(64) NOT NULL, 
	original_filename VARCHAR(512) NOT NULL, 
	stored_filename VARCHAR(512) NOT NULL, 
	extension VARCHAR(32) NOT NULL, 
	mime_type VARCHAR(128) NOT NULL, 
	size_bytes INTEGER NOT NULL, 
	sha256 VARCHAR(64) NOT NULL, 
	kind VARCHAR(64) NOT NULL, 
	path_on_disk TEXT NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS venue_files (
	id SERIAL NOT NULL, 
	venue_id VARCHAR(128) NOT NULL, 
	file_kind VARCHAR(64) NOT NULL, 
	path_on_disk TEXT NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS venues (
	id SERIAL NOT NULL, 
	venue_id VARCHAR(128) NOT NULL, 
	name VARCHAR(512) NOT NULL, 
	acronym VARCHAR(128) NOT NULL, 
	type VARCHAR(64) NOT NULL, 
	venue_family VARCHAR(256) NOT NULL, 
	quartile_or_rank TEXT NOT NULL, 
	q1_accessibility_class VARCHAR(128) NOT NULL, 
	publication_speed_category VARCHAR(128) NOT NULL, 
	review_rigor VARCHAR(128) NOT NULL, 
	official_url TEXT NOT NULL, 
	path_on_disk TEXT NOT NULL, 
	source_ref TEXT NOT NULL, 
	last_verified_at VARCHAR(64), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);
