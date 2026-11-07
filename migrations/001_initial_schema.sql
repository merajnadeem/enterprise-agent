CREATE EXTENSION IF NOT EXISTS "pgcrypto";


CREATE TABLE IF NOT EXISTS investigation_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id text NOT NULL,
    user_id text NOT NULL,
    idempotency_key text NOT NULL,
    request_hash text NOT NULL,
    question text NOT NULL,
    requested_sources JSONB NOT NULL,
    require_human_approval BOOLEAN NOT NULL DEFAULT TRUE,
    status TEXT NOT NULL DEFAULT 'pending',
    result JSONB,
    error_code TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_investigation_idempotency
        UNIQUE (tenant_id, idempotency_key),

    CONSTRAINT valid_investigation_status
        CHECK (
            status IN (
                'pending',
                'running',
                'waiting_approval',
                'succeeded',
                'failed'
            )
        )
);


CREATE TABLE outbox_events (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL
        REFERENCES investigation_jobs(id),

    event_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    published_at TIMESTAMPTZ,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE INDEX idx_investigation_tenant
ON investigation_jobs(tenant_id, created_at DESC);


CREATE INDEX idx_outbox_unpublished
ON outbox_events(created_at)
WHERE published_at IS NULL;
