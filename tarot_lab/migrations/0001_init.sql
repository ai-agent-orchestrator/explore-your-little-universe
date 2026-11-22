CREATE SCHEMA IF NOT EXISTS lumi;
CREATE SCHEMA IF NOT EXISTS langgraph;
CREATE TABLE lumi.profiles (
    profile_id uuid PRIMARY KEY, mbti text NOT NULL, zodiac_id text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE lumi.reading_sessions (
    session_id uuid PRIMARY KEY,
    owner_token_hash bytea NOT NULL CHECK (octet_length(owner_token_hash)=32),
    bootstrap_key_hash bytea UNIQUE,
    idempotency_key text NOT NULL, request_hash bytea NOT NULL,
    mbti text NOT NULL, zodiac_id text NOT NULL, question text NOT NULL,
    spread text NOT NULL CHECK (spread='three_card_reflection'),
    dataset_version text NOT NULL, mapping_version text NOT NULL, embedding_profile text NOT NULL,
    status text NOT NULL, error_code text,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(owner_token_hash,idempotency_key)
);
CREATE TABLE lumi.reading_draws (
    session_id uuid NOT NULL REFERENCES lumi.reading_sessions ON DELETE CASCADE,
    ordinal smallint NOT NULL CHECK (ordinal BETWEEN 0 AND 2),
    position text NOT NULL CHECK (position IN ('past','present','future')),
    card_id text NOT NULL, orientation text NOT NULL CHECK (orientation IN ('upright','reversed')),
    PRIMARY KEY(session_id,ordinal), UNIQUE(session_id,position), UNIQUE(session_id,card_id)
);
CREATE TABLE lumi.reading_reports (
    session_id uuid PRIMARY KEY REFERENCES lumi.reading_sessions ON DELETE CASCADE,
    report jsonb NOT NULL, evidence_ids jsonb NOT NULL, validation jsonb NOT NULL,
    model_id text NOT NULL, prompt_version text NOT NULL,
    completed_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE lumi.reading_events (
    session_id uuid NOT NULL REFERENCES lumi.reading_sessions ON DELETE CASCADE,
    sequence bigint NOT NULL, event_type text NOT NULL, payload jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(session_id,sequence)
);
