-- Organizations (tenants)
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- API Keys (service-to-service auth)
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    key_hash TEXT NOT NULL,
    key_prefix TEXT NOT NULL,
    name TEXT NOT NULL,
    scopes TEXT[] NOT NULL DEFAULT '{}',
    rate_limit_rpm INTEGER NOT NULL DEFAULT 60,
    is_active BOOLEAN NOT NULL DEFAULT true,
    last_used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ
);

-- Brand Context
CREATE TABLE IF NOT EXISTS brand_contexts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL,
    context_type TEXT NOT NULL,
    context_data JSONB NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(organization_id, context_type)
);

CREATE INDEX IF NOT EXISTS idx_brand_contexts_org ON brand_contexts(organization_id);

-- Generated Artifacts
CREATE TABLE IF NOT EXISTS generated_artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL,
    artifact_type TEXT NOT NULL,
    surface TEXT NOT NULL,
    subtype TEXT,
    spec_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'generating',
    content_url TEXT,
    content_json JSONB,
    slug TEXT UNIQUE,
    template_used TEXT,
    input_data JSONB NOT NULL,
    brand_context_snapshot JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_artifacts_org ON generated_artifacts(organization_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_slug ON generated_artifacts(slug) WHERE slug IS NOT NULL;

-- Jobs (async rendering)
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL,
    artifact_id UUID REFERENCES generated_artifacts(id),
    artifact_type TEXT NOT NULL,
    surface TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued',
    progress FLOAT,
    input_data JSONB NOT NULL,
    webhook_url TEXT,
    callback_metadata JSONB,
    error_message TEXT,
    provider_job_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_jobs_org ON jobs(organization_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status) WHERE status IN ('queued', 'rendering');

-- Landing Page Submissions
CREATE TABLE IF NOT EXISTS landing_page_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    artifact_id UUID NOT NULL REFERENCES generated_artifacts(id),
    slug TEXT NOT NULL,
    form_data JSONB NOT NULL,
    utm_params JSONB,
    organization_id UUID NOT NULL,
    campaign_id TEXT,
    anonymous_id TEXT,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_submissions_artifact ON landing_page_submissions(artifact_id);
CREATE INDEX IF NOT EXISTS idx_submissions_org ON landing_page_submissions(organization_id);

-- Usage Tracking
CREATE TABLE IF NOT EXISTS usage_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL,
    api_key_id UUID REFERENCES api_keys(id),
    artifact_type TEXT NOT NULL,
    surface TEXT NOT NULL,
    status TEXT NOT NULL,
    duration_ms INTEGER,
    claude_input_tokens INTEGER,
    claude_output_tokens INTEGER,
    provider_cost_cents INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_usage_org_time ON usage_events(organization_id, created_at);
