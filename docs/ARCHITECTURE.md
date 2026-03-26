# creative-engine-x — System Architecture

**Version:** 1.0.0
**Date:** 2026-03-26
**Status:** Design — Pre-Implementation

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Core Abstractions](#2-core-abstractions)
3. [Routing Model](#3-routing-model)
4. [Spec System](#4-spec-system)
5. [Request & Response Contracts](#5-request--response-contracts)
6. [Plugin Architecture](#6-plugin-architecture)
7. [Brand Context System](#7-brand-context-system)
8. [Landing Page Hosting](#8-landing-page-hosting)
9. [Auth Model](#9-auth-model)
10. [Storage Architecture](#10-storage-architecture)
11. [Async Job System](#11-async-job-system)
12. [Infrastructure](#12-infrastructure)
13. [Design Decisions](#13-design-decisions)

---

## 1. System Overview

creative-engine-x is a standalone, multi-tenant FastAPI service that generates marketing and sales artifacts for any consuming application. It receives structured input (content props, brand context, artifact+surface target, format preferences) and returns finished artifacts.

### Artifact Types

| Artifact Type | Description | Output |
|---|---|---|
| `pdf` | Lead magnets, reports, one-pagers | PDF binary |
| `html_page` | Landing pages, microsites — hosted and served | HTML + hosting |
| `document_slides` | LinkedIn carousels, pitch decks — slide-per-page | PDF binary |
| `video` | Ad spots, explainers, social clips | MP4/WebM file |
| `audio` | Voicemail drops, audio ads, narration | MP3/WAV file |
| `image` | Ad creatives, social graphics (briefs or generated) | JSON brief or image file |
| `structured_text` | Ad copy, video scripts, image briefs | JSON |
| `physical_mail` | Print-ready postcards, letters for Lob | PDF binary |

### Consumers

| Consumer | Primary Artifacts |
|---|---|
| **paid-engine-x** | Ad copy, landing pages, lead magnets, document ads, image briefs |
| **OEX-API** | Voicemail audio, direct mail postcards, landing pages |
| **Money Machine** | All artifact types |
| Future products | TBD |

### What Is Out of Scope

- Email/nurture sequences (handled by campaign execution layers)
- Ad platform API calls (stay in paid-engine-x)
- CRM sync (stays in paid-engine-x)
- Audience management (stays in paid-engine-x)

---

## 2. Core Abstractions

### 2.1 artifact_type

The category of output being produced. Each artifact type maps to a generation pipeline (LLM content generation) and a rendering pipeline (format conversion).

```
pdf | html_page | document_slides | video | audio | image | structured_text | physical_mail
```

### 2.2 surface

Where the artifact will be consumed or distributed. The surface determines platform-specific constraints (dimensions, character limits, duration limits, file format requirements).

```
generic | linkedin | meta | google | tiktok | youtube | web | voice_channel | direct_mail
```

### 2.3 format_spec

The combination of `artifact_type + surface` resolves to a `format_spec` — a YAML configuration file that defines all constraints, rendering pipeline, and I/O schemas for that combination.

```
artifact_type: structured_text
surface: linkedin
spec_id: structured_text__linkedin
```

### 2.4 Subtypes

Within a given `artifact_type + surface` combination, there may be further specialization. This is handled via a `subtype` field in the request, not by multiplying spec files.

Examples:
- `structured_text + generic` with `subtype: video_script` vs `subtype: image_brief`
- `pdf + generic` with `subtype: checklist` vs `subtype: ultimate_guide`
- `document_slides + linkedin` with `subtype: problem_solution` vs `subtype: listicle`

Subtypes are enumerated within each spec file. The spec defines subtype-specific constraints (e.g., word counts, slide counts) as nested config within the same file.

---

## 3. Routing Model

### 3.1 Two-Level Routing

Every request specifies `artifact_type` and `surface`. The router resolves these to:

1. **Spec** — loaded from `specs/{artifact_type}__{surface}.yaml`
2. **Generator** — the LLM content generation module (e.g., `generators/ad_copy.py`)
3. **Renderer** — the format conversion module (e.g., `renderers/pdf_renderer.py`)
4. **Provider** — the external service adapter (e.g., `providers/reportlab.py`, `providers/remotion.py`)

```
Request(artifact_type, surface)
  → SpecLoader.load(artifact_type, surface)
    → spec.generator_class → Generator
    → spec.renderer_class → Renderer
      → Renderer.provider → Provider
```

### 3.2 Granularity Decision

The routing model uses `artifact_type + surface` as the primary key, with `subtype` as an optional qualifier within a spec.

**Why not deeper granularity** (e.g., `structured_text + linkedin + sponsored_content`): Platform ad formats change frequently. Encoding format-level distinctions into the routing key means adding new spec files every time a platform adds a format. Instead, subtypes within a spec can be added by editing one YAML file. The spec system handles subtype-specific constraints (character limits, dimensions) as nested configuration.

**When to add a new surface**: Only when the platform imposes fundamentally different constraints that affect the rendering pipeline. LinkedIn sponsored content and LinkedIn message ads both produce structured text with similar constraints — they share a surface. But `voice_channel` (audio for phone systems) is fundamentally different from `web` (HTML for browsers) — they are separate surfaces.

### 3.3 Route Registry

On startup, the application scans `specs/` and builds a registry mapping `(artifact_type, surface)` → `FormatSpec`. Unknown combinations return 422 with available options.

```python
# src/routing/registry.py
class RouteRegistry:
    _specs: dict[tuple[str, str], FormatSpec]

    def resolve(self, artifact_type: str, surface: str) -> FormatSpec:
        key = (artifact_type, surface)
        if key not in self._specs:
            raise UnknownRouteError(artifact_type, surface, available=list(self._specs.keys()))
        return self._specs[key]
```

---

## 4. Spec System

### 4.1 Format: YAML Config Files

**Decision: YAML over Python dataclasses.**

Reasoning:
- Spec files are reference documents that non-engineers (product, design) may need to read and edit.
- YAML is more accessible and diffs cleanly in code review.
- Type safety is achieved by loading YAML into Pydantic models at startup — validation happens once on boot, not at request time.
- Adding a new artifact+surface combination requires only a new YAML file, no Python code changes to the routing layer.

### 4.2 Spec File Structure

Each spec lives at `src/specs/{artifact_type}__{surface}.yaml`:

```yaml
# Metadata
spec_id: structured_text__linkedin
artifact_type: structured_text
surface: linkedin
version: "1.0"

# Constraints
constraints:
  hard:                    # Platform-imposed, cannot override
    introductory_text_max_chars: 600
    headline_max_chars: 200
    description_max_chars: 100
  soft:                    # Opinionated defaults, consumer can override
    introductory_text_recommended_chars: 150
    headline_recommended_chars: 70
    tone: "professional"

# Subtypes (optional)
subtypes:
  sponsored_content:
    constraints:
      hard:
        introductory_text_max_chars: 600
  message_ad:
    constraints:
      hard:
        introductory_text_max_chars: 500

# Pipeline
pipeline:
  generator: generators.ad_copy.AdCopyGenerator
  renderer: null                          # structured_text has no renderer
  provider: null
  claude_model: claude-sonnet-4-20250514
  claude_temperature: 0.7

# Delivery
delivery:
  mode: sync                              # sync | async
  output_format: application/json
  storage: null                           # null (inline) | supabase | s3

# I/O Schemas (referenced, not inline)
schemas:
  input: schemas/structured_text__linkedin_input.json
  output: schemas/structured_text__linkedin_output.json
```

### 4.3 Hard vs Soft Constraints

| Type | Definition | Override Behavior |
|---|---|---|
| **Hard** | Platform-imposed limits. Exceeding them causes rejection or truncation by the platform. | Cannot be overridden. Post-generation validation truncates at word boundaries (porting `validate_ad_copy_limits()` from paid-engine-x). |
| **Soft** | Opinionated best-practice defaults. | Consumer can override per-request via `format_overrides` in the request body. |

### 4.4 Spec Loading

On application startup, `SpecLoader` reads all YAML files from `src/specs/`, validates each against the `FormatSpec` Pydantic model, and registers them in the `RouteRegistry`.

```python
# src/specs/loader.py
class SpecLoader:
    @staticmethod
    def load_all(specs_dir: Path) -> dict[tuple[str, str], FormatSpec]:
        specs = {}
        for yaml_file in specs_dir.glob("*.yaml"):
            raw = yaml.safe_load(yaml_file.read_text())
            spec = FormatSpec(**raw)  # Pydantic validation
            specs[(spec.artifact_type, spec.surface)] = spec
        return specs
```

---

## 5. Request & Response Contracts

### 5.1 Universal Request Schema

```python
class GenerateRequest(BaseModel):
    # Routing
    artifact_type: str                          # e.g., "structured_text"
    surface: str                                # e.g., "linkedin"
    subtype: str | None = None                  # e.g., "sponsored_content"

    # Content
    content_props: dict                         # Artifact-specific input (validated against spec schema)

    # Brand Context (one of)
    brand_context_id: str | None = None         # Reference: load from tenant_context by org_id
    brand_context: BrandContext | None = None    # Inline: full brand context object

    # Overrides
    format_overrides: dict | None = None        # Override soft constraints
    claude_model_override: str | None = None    # Override default model selection
    temperature_override: float | None = None   # Override default temperature

    # Metadata
    idempotency_key: str | None = None          # For retry safety
    webhook_url: str | None = None              # Completion callback for async jobs
    callback_metadata: dict | None = None       # Passed back in webhook payload
```

### 5.2 Sync Response

For artifacts where `delivery.mode == "sync"` in the spec:

```python
class GenerateResponse(BaseModel):
    artifact_id: str                            # UUID
    artifact_type: str
    surface: str
    status: Literal["completed", "failed"]
    content_url: str | None = None              # For rendered artifacts (PDF, HTML, audio)
    content: dict | None = None                 # For structured_text artifacts (inline JSON)
    content_preview: str | None = None          # First 500 chars for quick inspection
    spec_id: str                                # Which spec was used
    created_at: datetime
    error: ErrorDetail | None = None
```

### 5.3 Async Response

For artifacts where `delivery.mode == "async"` in the spec (video, potentially large PDFs):

```python
class AsyncGenerateResponse(BaseModel):
    job_id: str                                 # UUID
    artifact_type: str
    surface: str
    status: Literal["queued", "rendering"]
    poll_url: str                               # GET /jobs/{job_id}
    estimated_duration_seconds: int | None = None
    webhook_url: str | None = None              # Echo back
```

### 5.4 Job Status Response

```python
class JobStatusResponse(BaseModel):
    job_id: str
    artifact_id: str | None = None              # Set once rendering starts
    status: Literal["queued", "rendering", "completed", "failed"]
    progress: float | None = None               # 0.0-1.0 for video renders
    content_url: str | None = None              # Set on completion
    error: ErrorDetail | None = None
    created_at: datetime
    updated_at: datetime
```

### 5.5 Webhook Payload

When a job completes and `webhook_url` was provided:

```python
class WebhookPayload(BaseModel):
    event: Literal["job.completed", "job.failed"]
    job_id: str
    artifact_id: str | None
    artifact_type: str
    surface: str
    status: str
    content_url: str | None
    error: ErrorDetail | None
    callback_metadata: dict | None              # Echoed from request
    timestamp: datetime
```

### 5.6 Batch Generation

Consumers can request multiple artifacts in a single call. Each artifact+surface combination is processed independently and concurrently (porting the `asyncio.gather` pattern from paid-engine-x).

```python
class BatchGenerateRequest(BaseModel):
    items: list[GenerateRequest]                # Max 10 per batch
    brand_context_id: str | None = None         # Shared across items (can be overridden per item)
    brand_context: BrandContext | None = None

class BatchGenerateResponse(BaseModel):
    results: list[GenerateResponse | AsyncGenerateResponse]
    errors: list[BatchItemError] | None = None  # Per-item errors don't fail the batch
```

---

## 6. Plugin Architecture

### 6.1 Layer Overview

```
Request → Router → Generator → Renderer → Provider → Storage → Response
                      ↓              ↓           ↓
                  Claude API    Format Logic   External Service
```

| Layer | Responsibility | Interface | Examples |
|---|---|---|---|
| **Generator** | LLM content generation — takes content_props + brand_context, returns structured content | `GeneratorProtocol` | AdCopyGenerator, LeadMagnetGenerator, VideoScriptGenerator |
| **Renderer** | Converts structured content into final artifact format | `RendererProtocol` | PDFRenderer, HTMLRenderer, AudioRenderer, VideoRenderer |
| **Provider** | External service adapter behind a renderer | `ProviderProtocol` | ReportLabProvider, Jinja2Provider, ElevenLabsProvider, RemotionProvider, LobProvider |

### 6.2 Generator Interface

```python
class GeneratorProtocol(Protocol):
    async def generate(
        self,
        content_props: dict,
        brand_context: BrandContext,
        spec: FormatSpec,
        claude_client: ClaudeClient,
    ) -> GeneratedContent:
        """Generate structured content from input props and brand context."""
        ...
```

`GeneratedContent` is the intermediate representation — structured data (Pydantic model) that a renderer can consume. For `structured_text` artifacts, this is also the final output.

### 6.3 Renderer Interface

```python
class RendererProtocol(Protocol):
    async def render(
        self,
        content: GeneratedContent,
        spec: FormatSpec,
        brand_context: BrandContext,
    ) -> RenderedArtifact:
        """Convert generated content into the final artifact format."""
        ...

@dataclass
class RenderedArtifact:
    data: bytes                 # The rendered file bytes
    content_type: str           # MIME type (application/pdf, text/html, audio/mpeg, video/mp4)
    filename: str               # Suggested filename
    metadata: dict | None       # Renderer-specific metadata (page count, duration, etc.)
```

### 6.4 Provider Interface

```python
class ProviderProtocol(Protocol):
    async def execute(
        self,
        input_data: dict,
        config: dict,
    ) -> ProviderResult:
        """Execute the provider-specific operation."""
        ...
```

Providers are injected into renderers. A renderer may use multiple providers (e.g., `VideoRenderer` uses `RemotionProvider` for rendering and the built-in S3 client for storage).

### 6.5 Adding a New Artifact+Surface

To add support for a new combination:

1. Create `src/specs/{artifact_type}__{surface}.yaml` — define constraints, pipeline, schemas
2. If new generator logic is needed: create `src/generators/{name}.py` implementing `GeneratorProtocol`
3. If new rendering logic is needed: create `src/renderers/{name}.py` implementing `RendererProtocol`
4. If a new external service is needed: create `src/providers/{name}.py` implementing `ProviderProtocol`
5. Restart the application — the spec loader auto-discovers and registers the new route

Most new combinations reuse existing generators/renderers with different spec constraints. For example, adding `structured_text + tiktok` requires only a new spec file pointing to the existing `AdCopyGenerator`.

---

## 7. Brand Context System

### 7.1 Overview

Ported from paid-engine-x's `tenant_context` system (Extraction Audit Section 6), generalized for multi-tenant API access.

### 7.2 Context Access: By Reference + Inline (Both Supported)

**Decision: support both, with reference as the primary path.**

Reasoning:
- **By reference** (`brand_context_id`): Consumers pre-register brand context once, then reference it by org_id in every request. This is the primary path for production use — avoids sending large payloads on every request, enables context versioning, and ensures consistency across artifacts.
- **Inline** (`brand_context`): Consumers can pass the full brand context object in the request body. This supports testing, one-off generations, and consumers who manage their own brand data.
- When both are provided, inline takes precedence (allows per-request overrides on top of stored context).

### 7.3 BrandContext Model

```python
class BrandContext(BaseModel):
    # Identity
    organization_id: str | None = None      # Set by auth layer for by-reference
    company_name: str = ""
    industry: str | None = None

    # Voice
    brand_voice: str = ""
    brand_guidelines: BrandGuidelines | None = None

    # Positioning
    value_proposition: str = ""

    # Audience
    icp_definition: ICPDefinition | None = None
    target_persona: str = ""

    # Social Proof
    case_studies: list[CaseStudy] = []
    testimonials: list[Testimonial] = []
    customer_logos: list[str] = []

    # Competitive
    competitor_differentiators: list[str] = []

    # Campaign-specific (can be set per-request)
    angle: str | None = None
    objective: str | None = None
```

### 7.4 Database Schema

```sql
CREATE TABLE brand_contexts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL,
    context_type TEXT NOT NULL,          -- brand_guidelines, positioning, icp_definition, etc.
    context_data JSONB NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(organization_id, context_type)
);

CREATE INDEX idx_brand_contexts_org ON brand_contexts(organization_id);
```

### 7.5 Branding in Rendering

Brand context flows through the entire pipeline:
- **Generators** use company_name, voice, value_proposition, ICP, etc. to generate persona-specific content
- **Renderers** use brand colors (primary_color, secondary_color), font_family, and company_name for visual styling
- This matches the existing pattern in paid-engine-x (Extraction Audit Section 6.3)

---

## 8. Landing Page Hosting

### 8.1 Overview

Landing page hosting is a first-class capability. creative-engine-x generates HTML landing pages AND serves them publicly. This moves the entire `/lp/{slug}` system from paid-engine-x.

### 8.2 Routes

| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/lp/{slug}` | GET | Public | Serve rendered landing page HTML |
| `/lp/{slug}/submit` | POST | Public | Handle form submission |

### 8.3 Slug System

- Slugs are 12-character hex strings generated by `uuid.uuid4().hex[:12]`
- Stored on the `generated_artifacts` table alongside the artifact record
- No separate mapping table needed

### 8.4 Page Serving

```
GET /lp/{slug}
  1. Query generated_artifacts WHERE slug = :slug
  2. If content_url exists → fetch HTML from Supabase Storage
  3. Fallback → render from stored input_data via Jinja2
  4. Return HTMLResponse or 404
```

### 8.5 Form Submission

```
POST /lp/{slug}/submit
  1. Look up artifact by slug
  2. Parse form data (email, anonymous_id, UTMs)
  3. Insert into landing_page_submissions
  4. Fire RudderStack identify() + track("form_submitted")
  5. Return {"status": "ok"}
```

### 8.6 Analytics

- **Client-side**: RudderStack JS SDK injected into HTML templates. Fires `page()` on load, `identify()` + `track()` on form submit.
- **Server-side**: Python RudderStack calls on form submission for reliability.
- **UTM capture**: Hidden form fields populated from URL query params via JavaScript.

---

## 9. Auth Model

### 9.1 Service-to-Service (Primary)

API key authentication for machine-to-machine communication.

```
X-API-Key: cex_live_xxxxxxxxxxxx
```

API keys are scoped to an organization and stored in the `api_keys` table:

```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    key_hash TEXT NOT NULL,                 -- bcrypt hash of the key
    key_prefix TEXT NOT NULL,               -- First 8 chars for identification (cex_live_)
    name TEXT NOT NULL,                     -- Human-readable name ("paid-engine-x production")
    scopes TEXT[] NOT NULL DEFAULT '{}',    -- Optional scope restrictions
    rate_limit_rpm INTEGER NOT NULL DEFAULT 60,
    is_active BOOLEAN NOT NULL DEFAULT true,
    last_used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ
);
```

### 9.2 JWT (Optional, for direct access)

For consumers that already have a JWT-based auth system (e.g., frontend applications calling creative-engine-x directly):

```
Authorization: Bearer <jwt_token>
```

JWT validation extracts `organization_id` from claims. This mirrors the existing JWT pattern in paid-engine-x (Extraction Audit Section 9).

### 9.3 Public Routes

Landing page hosting routes (`/lp/*`) are public — no authentication required. This matches the existing pattern where `/lp/{slug}` is in `PUBLIC_PREFIXES`.

### 9.4 Middleware Chain

```
Request
  → RateLimitMiddleware (per API key)
  → AuthMiddleware (API key or JWT → organization_id)
  → TenantMiddleware (resolve org, inject into request state)
  → Route Handler
```

---

## 10. Storage Architecture

### 10.1 Supabase Storage (Primary — PDFs, HTML, Audio, Physical Mail)

Porting the existing Supabase Storage pattern from paid-engine-x (Extraction Audit Section 3.4).

**Bucket**: `artifacts` (public, auto-created if missing)

**Path Convention**:
```
{org_id}/{artifact_type}/{artifact_id}.{ext}
```

Examples:
```
org_abc123/pdf/art_456.pdf
org_abc123/html_page/art_789.html
org_abc123/audio/art_012.mp3
org_abc123/physical_mail/art_345.pdf
```

**URL Pattern**: `{SUPABASE_URL}/storage/v1/object/public/artifacts/{path}`

### 10.2 S3 (Video — via Remotion Lambda)

Remotion Lambda renders directly to S3. creative-engine-x doesn't upload video files — it reads them from the S3 bucket where Remotion Lambda wrote them.

**Bucket**: `remotion-renders-{env}` (private, presigned URLs for access)

**Path**: Managed by Remotion Lambda under `renders/{renderId}/`

After render completion, creative-engine-x either:
1. Returns the presigned S3 URL directly, or
2. Copies the rendered file to Supabase Storage for a consistent URL pattern

Decision: **Copy to Supabase** post-render. This keeps a single URL pattern for all artifacts, simplifies consumer integration, and avoids presigned URL expiration issues.

### 10.3 Database (Structured Text / JSON)

For `structured_text` artifacts (ad copy, video scripts, image briefs), the output is stored in the `content_json` column of `generated_artifacts` — no file storage needed.

---

## 11. Async Job System

### 11.1 Sync vs Async Boundary

**Decision: artifact-type-based, not time-based.**

Reasoning:
- Time-based thresholds are unpredictable — a "fast" PDF generation might spike if Claude is slow.
- Artifact-type-based boundaries are deterministic — consumers always know what to expect for each artifact type.
- This matches consumer integration patterns: you write sync handling once for ad copy, async handling once for video. You don't want the same endpoint sometimes returning sync and sometimes async.

| Mode | Artifact Types | Typical Duration |
|---|---|---|
| **Sync** | `structured_text`, `pdf`, `html_page`, `document_slides`, `image`, `physical_mail` | 2-30 seconds |
| **Async** | `video`, `audio` | 15-120 seconds |

Audio is async because ElevenLabs TTS for longer voicemail scripts can take 10-30 seconds, and we want a consistent pattern for all rendered media.

### 11.2 Job Lifecycle

```
POST /generate (async artifact)
  → Create job record (status: queued)
  → Return AsyncGenerateResponse with job_id
  → Background: dispatch to rendering pipeline
  → Update job (status: rendering, progress: 0.0-1.0)
  → On completion: update job (status: completed, content_url)
  → If webhook_url: POST webhook payload
```

### 11.3 Job Storage

```sql
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL,
    artifact_id UUID REFERENCES generated_artifacts(id),
    artifact_type TEXT NOT NULL,
    surface TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued',       -- queued, rendering, completed, failed
    progress FLOAT,
    input_data JSONB NOT NULL,                   -- Full request for replay/debugging
    webhook_url TEXT,
    callback_metadata JSONB,
    error_message TEXT,
    provider_job_id TEXT,                         -- e.g., Remotion Lambda renderId
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX idx_jobs_org ON jobs(organization_id);
CREATE INDEX idx_jobs_status ON jobs(status) WHERE status IN ('queued', 'rendering');
```

### 11.4 Background Processing

For the initial implementation: FastAPI `BackgroundTasks` for job dispatch. The rendering pipeline runs in-process.

For scale: migrate to a proper task queue (e.g., Celery with Redis, or Railway's built-in workers). The job table is the source of truth regardless of the task execution mechanism.

### 11.5 Progress Polling

```
GET /jobs/{job_id}
  → Return JobStatusResponse
```

For video renders, progress is updated by polling Remotion Lambda's `getRenderProgress()` endpoint.

---

## 12. Infrastructure

### 12.1 Stack

| Component | Technology | Notes |
|---|---|---|
| API Framework | FastAPI (Python 3.12+) | Matches paid-engine-x stack |
| Database | Supabase PostgreSQL | Managed, existing infra |
| File Storage | Supabase Storage | PDFs, HTML, audio, physical mail |
| Video Storage | AWS S3 (via Remotion Lambda) | Copied to Supabase post-render |
| LLM | Anthropic Claude (Opus + Sonnet) | Via anthropic Python SDK |
| Video Rendering | Remotion Lambda | Separate Node.js project, deployed to AWS |
| Audio Rendering | ElevenLabs REST API | Via elevenlabs Python SDK or httpx |
| PDF Rendering | ReportLab | Python, in-process |
| HTML Rendering | Jinja2 | Python, in-process |
| Secrets | Doppler | Matches paid-engine-x pattern |
| Deployment | Railway | Matches paid-engine-x pattern |
| Analytics | RudderStack | Landing page events |

### 12.2 Remotion as Separate Service

Remotion is a Node.js/React framework. creative-engine-x is Python. The integration architecture:

```
creative-engine-x (Python/FastAPI)
  → calls Remotion Lambda API (via @remotion/lambda-client or direct AWS SDK)
    → Remotion Lambda renders video on AWS
      → writes MP4 to S3
  ← polls getRenderProgress() for status
  ← on completion: copies MP4 from S3 to Supabase Storage
```

The Remotion project (React compositions + templates) is a separate repository/directory:
- `creative-engine-x-remotion/` — Node.js project with all video composition templates
- Deployed to AWS Lambda via `deploySite()` + `deployFunction()` (Remotion CLI/API)
- creative-engine-x calls it by passing `inputProps` (content, brand colors, dimensions)

### 12.3 Repository Structure

```
creative-engine-x-api/
├── src/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app, middleware, router registration
│   ├── config.py                   # Settings (env vars via pydantic-settings)
│   ├── dependencies.py             # DI: get_claude, get_supabase, get_current_org
│   │
│   ├── routing/
│   │   ├── __init__.py
│   │   ├── registry.py             # RouteRegistry — spec → generator/renderer resolution
│   │   └── router.py               # /generate, /generate/batch, /jobs/{id}
│   │
│   ├── specs/
│   │   ├── __init__.py
│   │   ├── loader.py               # YAML → FormatSpec Pydantic models
│   │   ├── models.py               # FormatSpec, Constraint, Pipeline dataclasses
│   │   ├── structured_text__linkedin.yaml
│   │   ├── structured_text__meta.yaml
│   │   ├── structured_text__google.yaml
│   │   ├── structured_text__generic.yaml   # video_script, image_brief subtypes
│   │   ├── pdf__generic.yaml
│   │   ├── html_page__web.yaml
│   │   ├── document_slides__linkedin.yaml
│   │   ├── video__meta.yaml
│   │   ├── video__tiktok.yaml
│   │   ├── video__generic.yaml
│   │   ├── audio__voice_channel.yaml
│   │   └── physical_mail__direct_mail.yaml
│   │
│   ├── generators/
│   │   ├── __init__.py
│   │   ├── base.py                 # GeneratorProtocol, base prompt patterns
│   │   ├── ad_copy.py              # Ported from paid-engine-x (BJC-171)
│   │   ├── lead_magnet.py          # Ported from paid-engine-x (BJC-169)
│   │   ├── landing_page.py         # Ported from paid-engine-x (BJC-170)
│   │   ├── document_slides.py      # Ported from paid-engine-x (BJC-174)
│   │   ├── video_script.py         # Ported from paid-engine-x (BJC-175)
│   │   ├── case_study.py           # Ported from paid-engine-x (BJC-176)
│   │   ├── image_brief.py          # Ported from paid-engine-x (BJC-173)
│   │   ├── audio_script.py         # New — voicemail/narration text generation
│   │   └── physical_mail.py        # New — postcard/letter content generation
│   │
│   ├── renderers/
│   │   ├── __init__.py
│   │   ├── base.py                 # RendererProtocol
│   │   ├── pdf_renderer.py         # Lead magnets, physical mail → PDF via ReportLab
│   │   ├── slide_renderer.py       # Document slides → PDF via ReportLab
│   │   ├── html_renderer.py        # Landing pages → HTML via Jinja2
│   │   ├── video_renderer.py       # Video → MP4 via Remotion Lambda
│   │   └── audio_renderer.py       # Audio → MP3 via ElevenLabs
│   │
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── base.py                 # ProviderProtocol
│   │   ├── reportlab_provider.py   # ReportLab PDF generation
│   │   ├── jinja2_provider.py      # Jinja2 HTML rendering
│   │   ├── remotion_provider.py    # Remotion Lambda render trigger + progress
│   │   ├── elevenlabs_provider.py  # ElevenLabs TTS
│   │   └── lob_provider.py         # Lob print-ready PDF generation (future)
│   │
│   ├── brand/
│   │   ├── __init__.py
│   │   ├── models.py               # BrandContext, BrandGuidelines, ICPDefinition, etc.
│   │   ├── service.py              # build_brand_context(org_id, supabase)
│   │   └── router.py               # CRUD for brand context
│   │
│   ├── landing_pages/
│   │   ├── __init__.py
│   │   └── router.py               # GET /lp/{slug}, POST /lp/{slug}/submit
│   │
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── middleware.py            # API key + JWT auth middleware
│   │   ├── models.py               # APIKey, Organization
│   │   └── service.py              # Key validation, rate limiting
│   │
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── claude_client.py        # Anthropic Claude wrapper
│   │   ├── supabase_client.py      # Supabase client singleton
│   │   └── rudderstack.py          # RudderStack server-side calls
│   │
│   ├── storage/
│   │   ├── __init__.py
│   │   └── service.py              # Upload to Supabase Storage, S3 copy
│   │
│   ├── jobs/
│   │   ├── __init__.py
│   │   ├── models.py               # Job status models
│   │   ├── service.py              # Job lifecycle management
│   │   └── router.py               # GET /jobs/{id}
│   │
│   ├── shared/
│   │   ├── __init__.py
│   │   ├── errors.py               # Error types (ported from paid-engine-x)
│   │   ├── models.py               # Common response models
│   │   └── pagination.py           # Pagination utilities
│   │
│   └── templates/                  # Jinja2 HTML templates for landing pages
│       ├── lead_magnet_download.html
│       ├── case_study.html
│       ├── webinar.html
│       └── demo_request.html
│
├── docs/
│   ├── ARCHITECTURE.md             # This document
│   └── specs/                      # Human-readable spec reference docs
│       ├── pdf__generic.md
│       ├── document_slides__linkedin.md
│       └── ...
│
├── tests/
├── Dockerfile
├── pyproject.toml
├── railway.toml
└── README.md
```

---

## 13. Design Decisions

### Decision 1: Routing Model Granularity

**Choice**: `artifact_type + surface` as routing key, with `subtype` as optional qualifier.

**Reasoning**: Two-level routing (`artifact_type + surface`) captures the meaningful architectural boundary — what rendering pipeline to use and what platform constraints to apply. Going deeper (e.g., `structured_text + linkedin + sponsored_content`) over-indexes on platform ad format taxonomy, which changes frequently. Subtypes within a spec handle format-level variation without multiplying routing entries. Adding a new LinkedIn ad format is a one-line YAML addition, not a new spec file + routing entry.

### Decision 2: Spec Files — YAML

**Choice**: YAML config files, loaded into Pydantic models at startup.

**Reasoning**: YAML gives accessibility (product/design can read and edit constraints), clean diffs in PRs, and zero-code addition of new artifact+surface combinations. Type safety is not sacrificed — Pydantic validates every spec on boot. If a YAML file has invalid structure, the application fails to start with a clear error. The alternative (Python dataclasses registered in code) provides marginally better IDE support but requires code changes and deploys for constraint tweaks.

### Decision 3: Sync vs Async — Artifact-Type-Based

**Choice**: Sync for text/PDF/HTML/slides/image/mail, async for video/audio.

**Reasoning**: Deterministic behavior over adaptive thresholds. Consumers integrate differently for sync vs async responses — they need to know at development time, not at runtime, which pattern to use. Video rendering via Remotion Lambda is inherently async (30-120 seconds). Audio via ElevenLabs could sometimes be fast (<5s for short text) but is grouped with video for consistency — all rendered media is async, all generated text/documents are sync. This maps cleanly to consumer architecture: "if I'm requesting media that requires an external render service, I'll get a job ID."

### Decision 4: Remotion Integration — Lambda

**Choice**: Remotion Lambda (creative-engine-x calls Lambda API directly from Python).

**Reasoning**:
- **Not a separate Node.js render service**: Running Remotion rendering on a Node.js server requires Chrome + FFmpeg installed, high CPU/memory, and doesn't scale horizontally without significant infrastructure. This is viable for dev/preview but not production multi-tenant rendering.
- **Not Cloud Run**: The team is AWS-aligned (Railway + Supabase + existing AWS accounts). Cloud Run adds GCP dependency.
- **Lambda fits**: Serverless, scales to zero, handles burst rendering (multiple tenants rendering simultaneously), built-in S3 output, webhook support, progress polling. The Remotion Lambda API is mature and well-documented.
- **Python calling Lambda**: The `@remotion/lambda-client` package is Node.js, but the underlying calls are HTTP requests to AWS Lambda. creative-engine-x uses `boto3` (AWS SDK for Python) to invoke Lambda directly, or wraps the Remotion Lambda REST API. The Remotion team documents the Lambda function's expected input format.

### Decision 5: Video Template Management — Single Remotion Project

**Choice**: One Remotion project with all composition templates, parameterized via `inputProps`.

**Reasoning**: Per the Remotion docs (Section 16 — multi-tenant patterns), the recommended approach for multi-tenant video generation is a single Remotion project where compositions accept dynamic input props. Tenant-specific branding (colors, fonts, logos, copy) is passed as `inputProps` at render time, not baked into the template code. This means:
- One `deploySite()` call deploys all templates
- One `deployFunction()` deploys the Lambda function
- New video templates are new `<Composition>` components in the same project
- Template versioning is Git-based — deploy a new site version when templates change
- creative-engine-x passes `compositionId` (which template) + `inputProps` (content + branding) to `renderMediaOnLambda()`

### Decision 6: Image Generation — Briefs Only (For Now)

**Choice**: creative-engine-x generates structured image briefs (JSON), not actual images. Image generation is deferred to a future phase.

**Reasoning**: The existing system produces image briefs — structured JSON describing the desired image (concept, dimensions, color palette, text overlay, mood). This is already consumed by downstream systems or human designers. Adding actual image generation (via DALL-E, Midjourney API, Stable Diffusion) introduces a new provider dependency, quality control challenges (generated images often need human review), and cost considerations. The architecture supports adding an `ImageProvider` behind the `ImageRenderer` later — when we do, the spec file just updates `pipeline.renderer` and `pipeline.provider` and the generator's output schema gains an `image_url` field. No architectural changes needed.

### Decision 7: Physical Mail — Generate Only, Don't Send

**Choice**: creative-engine-x generates print-ready PDFs and returns them. It does not call the Lob API to mail them.

**Reasoning**: Sending physical mail is a campaign execution action, not an artifact generation action. creative-engine-x is infrastructure — it produces artifacts. The consumer (OEX-API, Money Machine) decides when and whether to actually mail. This matches the pattern for all other artifacts: creative-engine-x generates ad copy but doesn't post it to LinkedIn; it generates landing page HTML but the consumer decides which campaigns link to it. The `LobProvider` in creative-engine-x handles Lob's print-ready PDF specification requirements (bleed, safe zones, dimensions) but doesn't call the send endpoint.

### Decision 8: Brand Context — By Reference + Inline

**Choice**: Support both, inline takes precedence.

**Reasoning**: By-reference is the production path — consumers register brand context once, then reference it by organization. Inline is essential for: (1) testing/development without database setup, (2) one-off generations where the consumer manages its own brand data, (3) per-request overrides (e.g., A/B testing different value propositions). When both are provided, inline wins — this gives consumers a predictable override mechanism. The brand context system is ported from paid-engine-x's `tenant_context` table (Extraction Audit Section 6) with the addition of inline support.

---

## Appendix A: Database Schema (Full)

```sql
-- Organizations (tenants)
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- API Keys (service-to-service auth)
CREATE TABLE api_keys (
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
CREATE TABLE brand_contexts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL,
    context_type TEXT NOT NULL,
    context_data JSONB NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(organization_id, context_type)
);

-- Generated Artifacts
CREATE TABLE generated_artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL,
    artifact_type TEXT NOT NULL,
    surface TEXT NOT NULL,
    subtype TEXT,
    spec_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'generating',   -- generating, completed, failed
    content_url TEXT,                             -- Supabase Storage URL
    content_json JSONB,                          -- For structured_text artifacts
    slug TEXT UNIQUE,                            -- For landing pages
    template_used TEXT,
    input_data JSONB NOT NULL,                   -- Full request for replay
    brand_context_snapshot JSONB,                -- Snapshot of brand context used
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_artifacts_org ON generated_artifacts(organization_id);
CREATE INDEX idx_artifacts_slug ON generated_artifacts(slug) WHERE slug IS NOT NULL;

-- Jobs (async rendering)
CREATE TABLE jobs (
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

CREATE INDEX idx_jobs_org ON jobs(organization_id);
CREATE INDEX idx_jobs_status ON jobs(status) WHERE status IN ('queued', 'rendering');

-- Landing Page Submissions
CREATE TABLE landing_page_submissions (
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

CREATE INDEX idx_submissions_artifact ON landing_page_submissions(artifact_id);
CREATE INDEX idx_submissions_org ON landing_page_submissions(organization_id);

-- Usage Tracking
CREATE TABLE usage_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL,
    api_key_id UUID REFERENCES api_keys(id),
    artifact_type TEXT NOT NULL,
    surface TEXT NOT NULL,
    status TEXT NOT NULL,                        -- completed, failed
    duration_ms INTEGER,
    claude_input_tokens INTEGER,
    claude_output_tokens INTEGER,
    provider_cost_cents INTEGER,                 -- ElevenLabs chars, Remotion render cost, etc.
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_usage_org_time ON usage_events(organization_id, created_at);
```

---

## Appendix B: Environment Variables

```
# Core
DATABASE_URL=postgresql://...
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=...

# AI
ANTHROPIC_API_KEY=...

# Video
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
REMOTION_FUNCTION_NAME=remotion-render-...
REMOTION_SERVE_URL=https://remotionlambda-xxx.s3.amazonaws.com/sites/xxx

# Audio
ELEVENLABS_API_KEY=...
ELEVENLABS_DEFAULT_VOICE_ID=...

# Analytics
RUDDERSTACK_WRITE_KEY=...
RUDDERSTACK_DATA_PLANE_URL=...

# Auth
API_KEY_SALT=...
JWT_SECRET=...

# Optional future
LOB_API_KEY=...
```
