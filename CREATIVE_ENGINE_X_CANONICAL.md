# creative-engine-x-api -- Canonical Reference

**Generated:** 2026-04-04
**Repo:** creative-engine-x-api
**Branch:** bencrane/deep-dive-audit (off main @ 93182ed)
**Version:** 0.1.0.0

---

## Section 1: Repository Overview

### Directory Tree

```
.
├── .claude/CLAUDE.md
├── .env.example
├── .gitignore
├── CHANGELOG.md
├── Dockerfile
├── VERSION
├── creative-engine-x-remotion/
│   ├── .gitignore
│   ├── __tests__/
│   │   ├── compositions.test.ts
│   │   ├── deploy.test.ts
│   │   ├── inputProps.test.ts
│   │   └── shared-components.test.ts
│   ├── deploy.ts
│   ├── iam-setup.ts
│   ├── package-lock.json
│   ├── package.json
│   ├── remotion.config.ts
│   ├── src/
│   │   ├── Root.tsx
│   │   ├── compositions/
│   │   │   ├── GenericVideo.tsx
│   │   │   ├── MetaAd.tsx
│   │   │   ├── TikTokAd.tsx
│   │   │   └── shared/
│   │   │       ├── BackgroundPattern.tsx
│   │   │       ├── BrandBar.tsx
│   │   │       ├── CTASlide.tsx
│   │   │       ├── SceneTransition.tsx
│   │   │       ├── TextOverlay.tsx
│   │   │       └── index.ts
│   │   ├── index.ts
│   │   └── schemas/
│   │       └── inputProps.ts
│   ├── tsconfig.json
│   └── vitest.config.ts
├── docs/
│   ├── ARCHITECTURE.md
│   ├── FIGMA_API_REFERENCE.md
│   ├── FIGMA_EXTRACTION_REPORT.md
│   ├── FIGMA_IMPLEMENTATION_AUDIT.md
│   ├── LOB_MAILER_CONSTRAINTS.md
│   ├── POST_SHIP_ENGINEERING_AUDIT.md
│   ├── SCAFFOLD_MASTERS.md
│   ├── figma-extraction-report.json
│   ├── figma-validation-summary.json
│   ├── lob-templates/ (14 PDF template files)
│   └── specs/ (14 YAML files -- mirrors src/specs/)
├── migrations/
│   └── 001_initial_schema.sql
├── pyproject.toml
├── railway.toml
├── scaffolds/ (14 HTML scaffold visualization files)
├── scripts/
│   ├── data/figma-metadata.txt
│   └── validate_figma_zones.py
├── src/
│   ├── __init__.py
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── middleware.py
│   │   ├── models.py
│   │   ├── router.py
│   │   └── service.py
│   ├── brand/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── router.py
│   │   └── service.py
│   ├── config.py
│   ├── db.py
│   ├── dependencies.py
│   ├── extractors/
│   │   ├── __init__.py
│   │   └── youtube.py
│   ├── generators/
│   │   ├── __init__.py
│   │   ├── ad_copy.py
│   │   ├── audio_script.py
│   │   ├── base.py
│   │   ├── case_study.py
│   │   ├── document_slides.py
│   │   ├── image_brief.py
│   │   ├── landing_page.py
│   │   ├── lead_magnet.py
│   │   ├── physical_mail.py
│   │   └── video_script.py
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── claude_client.py
│   │   ├── rudderstack.py
│   │   └── supabase_client.py
│   ├── jobs/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── router.py
│   │   └── service.py
│   ├── landing_pages/
│   │   ├── __init__.py
│   │   └── router.py
│   ├── main.py
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── orchestrator.py
│   │   └── registry.py
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── elevenlabs_provider.py
│   │   ├── jinja2_provider.py
│   │   ├── remotion_provider.py
│   │   └── reportlab_provider.py
│   ├── renderers/
│   │   ├── __init__.py
│   │   ├── audio_renderer.py
│   │   ├── base.py
│   │   ├── html_renderer.py
│   │   ├── pdf_renderer.py
│   │   ├── slide_renderer.py
│   │   └── video_renderer.py
│   ├── routing/
│   │   ├── __init__.py
│   │   ├── registry.py
│   │   └── router.py
│   ├── scaffolds/
│   │   ├── __init__.py
│   │   └── (14 JSON scaffold files)
│   ├── shared/
│   │   ├── __init__.py
│   │   ├── errors.py
│   │   ├── models.py
│   │   └── text.py
│   ├── specs/
│   │   ├── __init__.py
│   │   ├── loader.py
│   │   ├── models.py
│   │   └── (13 YAML spec files)
│   ├── storage/
│   │   ├── __init__.py
│   │   └── service.py
│   └── templates/
│       ├── case_study.html
│       ├── demo_request.html
│       ├── lead_magnet_download.html
│       └── webinar.html
└── tests/ (22 test files)
```

### File Counts

| Category | Count |
|---|---|
| Python source files (src/) | 47 |
| Python test files (tests/) | 22 |
| YAML spec files (src/specs/) | 13 |
| JSON scaffold files (src/scaffolds/) | 14 |
| HTML template files (src/templates/) | 4 |
| HTML scaffold visualizations (scaffolds/) | 14 |
| TypeScript/TSX (creative-engine-x-remotion/) | 14 |
| Markdown docs | 8 |
| Config files | 8 |
| SQL migrations | 1 |
| **Total files (excluding .git, __pycache__)** | **~160** |

### Git Status

- **Last commit:** 93182ed (2026-03-28) -- `feat: migrate auth from HS256/python-jose to EdDSA/PyJWT with JWKS`
- **Total commits:** 56
- **Current version:** 0.1.0.0
- **Branches:** main, bencrane/deep-dive-audit (this audit)

### Deployment Configuration

**Dockerfile:**
```dockerfile
FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y \
    apt-transport-https ca-certificates curl gnupg \
    && curl -sLf --retry 3 --tlsv1.2 --proto "=https" \
       'https://packages.doppler.com/public/cli/gpg.DE2A7741A397C129.key' | \
       gpg --dearmor -o /usr/share/keyrings/doppler-archive-keyring.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/doppler-archive-keyring.gpg] https://packages.doppler.com/public/cli/deb/debian any-version main" > \
       /etc/apt/sources.list.d/doppler-cli.list \
    && apt-get update && apt-get install -y doppler \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml .
RUN pip install --no-cache-dir .
COPY src/ src/
EXPOSE 8080
CMD ["doppler", "run", "--", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

**railway.toml:**
```toml
[build]
builder = "dockerfile"
dockerfilePath = "Dockerfile"

[deploy]
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3
```

**Doppler:** Secrets are injected via `doppler run --` in the CMD. No `.doppler.yaml` committed (gitignored).

---

## Section 2: Application Entry Point & Structure

### `src/main.py`

**Framework:** FastAPI with async `lifespan` context manager.

**Startup sequence:**
1. `init_pool()` -- creates asyncpg connection pool (min=2, max=10) from `DATABASE_URL`
2. `SpecLoader.load_all()` -- loads all 13 YAML spec files from `src/specs/`
3. `registry.register(specs)` -- populates the route registry with `(artifact_type, surface) -> FormatSpec` mappings

**Shutdown:** `close_pool()` -- closes asyncpg pool.

**App:** `FastAPI(title="creative-engine-x-api", lifespan=lifespan)`

**CORS Middleware:**
- `allow_origins`: `["http://localhost:3000", "http://localhost:3001"]`
- `allow_credentials=True`, all methods, all headers

**Auth Middleware:** `AuthMiddleware` (custom Starlette BaseHTTPMiddleware) -- see Section 3.

**Routers:**
| Router | Prefix | Source |
|---|---|---|
| `generate_router` | (none) | `src.routing.router` -- `/generate`, `/generate/batch`, `/artifacts/{id}` |
| `brand_router` | `/brand-contexts` | `src.brand.router` |
| `jobs_router` | (none) | `src.jobs.router` -- `/jobs/{job_id}` |
| `auth_router` | `/auth` | `src.auth.router` |
| `landing_pages_router` | `/lp` | `src.landing_pages.router` |

**Health endpoint:** `GET /health` -> `{"status": "ok", "service": "creative-engine-x"}`

**Exception handlers:**
| Exception | Status | Code |
|---|---|---|
| `AuthenticationError` | 401 | `authentication_error` |
| `RateLimitExceededError` | 429 | `rate_limit_exceeded` |
| `UnknownRouteError` | 422 | `unknown_route` (includes available routes) |
| `SpecNotFoundError` | 404 | `spec_not_found` |
| `JobNotFoundError` | 404 | `job_not_found` |
| `ValidationError` | 422 | `validation_error` |

### Auth Middleware

**Public prefixes (no auth required):** `/health`, `/lp/`, `/docs`, `/openapi.json`

**Auth flow:**
1. Check `X-API-Key` header -> `verify_api_key()` (8-char prefix lookup, SHA256 pre-hash + bcrypt verify, expiry check) -> sets `request.state.organization_id`, `api_key_id`, `rate_limit_rpm`
2. Check `Authorization: Bearer <token>` -> `verify_jwt()` (EdDSA algorithm, JWKS from `https://api.authengine.dev/api/auth/jwks`) -> sets `request.state.organization_id`, `api_key_id=None`, `rate_limit_rpm=60`
3. Else -> 401 `AuthenticationError`
4. `resolve_organization(org_id, pool)` -> `SELECT * FROM organizations WHERE id = $1` -> sets `request.state.organization`

**Rate limiting:** In-memory sliding window per `api_key_id`, 60-second window, configurable RPM per key.

### Multi-tenant context

Organization is resolved from auth (API key -> `organization_id`, JWT -> `org_id` claim). Stored in `request.state.organization`. All queries are scoped by `organization_id`.

---

## Section 3: API Endpoints -- Complete Inventory

### Generation Endpoints

#### `POST /generate`

The primary content generation endpoint. Handles both sync and async artifact types.

**Request body:**
```python
class GenerateRequest(BaseModel):
    artifact_type: str                      # e.g., "structured_text", "pdf", "video"
    surface: str                            # e.g., "linkedin", "meta", "generic", "web"
    subtype: str | None = None              # e.g., "video_script", "checklist", "problem_solution"
    content_props: dict                     # Artifact-specific input
    brand_context_id: str | None = None     # Load stored brand context by org_id
    brand_context: dict | None = None       # Inline brand context (takes precedence)
    format_overrides: dict | None = None    # Override soft constraints
    claude_model_override: str | None = None
    temperature_override: float | None = None
    idempotency_key: str | None = None
    webhook_url: str | None = None          # For async jobs
    callback_metadata: dict | None = None   # Echoed in webhook
```

**Sync response** (for structured_text, pdf, html_page, document_slides, image, physical_mail):
```python
class GenerateResponse(BaseModel):
    artifact_id: str
    artifact_type: str
    surface: str
    status: Literal["completed", "failed"]
    content_url: str | None = None          # Supabase Storage URL
    content: dict | None = None             # Inline JSON for structured_text
    content_preview: str | None = None      # First 500 chars
    spec_id: str
    created_at: datetime
    error: ErrorDetail | None = None
```

**Async response** (for video, audio):
```python
class AsyncGenerateResponse(BaseModel):
    job_id: str
    artifact_type: str
    surface: str
    status: Literal["queued", "rendering"]
    poll_url: str                           # GET /jobs/{job_id}
    estimated_duration_seconds: int | None = None
    webhook_url: str | None = None
```

**Auth:** Required (API key or JWT).

**Implementation:** Resolves spec from `(artifact_type, surface)`. Resolves brand context (inline > by-reference > empty). If artifact type is async (`video`, `audio`), creates job + background task and returns immediately. Otherwise, runs full sync pipeline (generate -> render -> upload -> DB) and returns result.

#### `POST /generate/batch`

Processes up to 10 items in one call with shared brand context.

```python
class BatchGenerateRequest(BaseModel):
    items: list[GenerateRequest]            # Max 10 processed
    brand_context_id: str | None = None     # Shared across items
    brand_context: dict | None = None       # Shared across items

class BatchGenerateResponse(BaseModel):
    results: list[GenerateResponse | AsyncGenerateResponse]
    errors: list[BatchItemError] | None = None
```

**Auth:** Required.

#### `GET /artifacts/{artifact_id}`

Fetch a previously generated artifact by ID.

```python
class ArtifactResponse(BaseModel):
    id: str
    artifact_type: str
    surface: str
    subtype: str | None = None
    spec_id: str
    status: str
    content_url: str | None = None
    content_json: dict | None = None
    slug: str | None = None
    template_used: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
```

**Auth:** Required. Checks org ownership.

### Job Endpoints

#### `GET /jobs/{job_id}`

Poll async job status.

```python
class JobStatusResponse(BaseModel):
    job_id: str
    artifact_id: str | None = None
    status: Literal["queued", "rendering", "completed", "failed"]
    progress: float | None = None           # 0.0-1.0
    content_url: str | None = None
    error: ErrorDetail | None = None
    created_at: datetime
    updated_at: datetime
```

**Auth:** Required.

### Brand Context Endpoints

#### `POST /brand-contexts`

Upsert brand context (type "identity").

```python
class UpsertBrandContextRequest(BaseModel):
    context_data: dict
```

**Auth:** Required.

#### `GET /brand-contexts/{org_id}`

Build full BrandContext from all stored rows for an org.

**Auth:** Required.

#### `PUT /brand-contexts/{org_id}/{context_type}`

Upsert a specific context type (identity, brand_guidelines, positioning, icp_definition, case_studies, testimonials).

**Auth:** Required.

#### `DELETE /brand-contexts/{org_id}/{context_type}`

Delete a specific context type.

**Auth:** Required. Returns 204.

### Auth Endpoints

#### `POST /auth/api-keys`

Create a new API key for the org.

```python
class CreateAPIKeyRequest(BaseModel):
    name: str
    scopes: list[str] = []
    rate_limit_rpm: int = 60

class CreateAPIKeyResponse(BaseModel):
    raw_key: str                            # cex_live_{64 hex chars} -- shown once
    key: APIKeyRecord
```

**Auth:** Required.

#### `DELETE /auth/api-keys/{key_id}`

Revoke an API key (soft delete -- sets `is_active=false`).

**Auth:** Required. Returns 204.

### Landing Page Endpoints

#### `GET /lp/{slug}`

Serve a generated landing page by slug.

**Auth:** Public (no auth required).

**Implementation:**
1. Query `generated_artifacts` by slug
2. If `content_url` exists -> fetch HTML from Supabase Storage
3. Fallback -> render from `input_data` via Jinja2
4. Return HTMLResponse or 404

#### `POST /lp/{slug}/submit`

Handle form submission on a landing page.

**Auth:** Public (no auth required).

**Implementation:**
1. Look up artifact by slug
2. Parse form data + UTM params
3. INSERT into `landing_page_submissions`
4. Fire RudderStack `identify()` (if email present) + `track("form_submitted")`
5. Return `{"status": "ok"}`

### Health Endpoint

#### `GET /health`

**Auth:** Public.
**Response:** `{"status": "ok", "service": "creative-engine-x"}`

---

## Section 4: Cold Email Copy Generation -- THE DEEP DIVE

### Does cold email generation exist in this repo?

**No.** There is **zero code** in this repository that generates cold email copy, cold email sequences, or any email content whatsoever.

### Evidence of absence

1. **No email generator.** The `src/generators/` directory contains 9 generators:
   - `ad_copy.py` (LinkedIn, Meta, Google ad copy)
   - `audio_script.py` (voicemail/narration scripts)
   - `case_study.py` (case study content)
   - `document_slides.py` (LinkedIn carousels)
   - `image_brief.py` (image briefs for designers)
   - `landing_page.py` (landing page content)
   - `lead_magnet.py` (lead magnets -- checklists, guides, reports)
   - `physical_mail.py` (postcards and letters)
   - `video_script.py` (video ad scripts)

   **None** of these generate cold email copy. None contain the words "email", "sequence", "step", "follow-up", "cold", "outbound", "campaign copy", or "nurture" in their prompt templates.

2. **No email-related spec.** The 13 YAML spec files map to these artifact_type+surface combinations:
   - `structured_text__linkedin`, `structured_text__meta`, `structured_text__google` (ad copy)
   - `structured_text__generic__image_brief`, `structured_text__generic__video_script` (subtypes)
   - `pdf__generic` (lead magnets)
   - `html_page__web` (landing pages)
   - `document_slides__linkedin` (carousels)
   - `audio__voice_channel` (voicemail)
   - `video__generic`, `video__meta`, `video__tiktok` (video)
   - `physical_mail__direct_mail` (postcards/letters)

   There is no `structured_text__email`, `email__cold`, `email__sequence`, or anything similar.

3. **Architecture doc explicitly excludes email.** From `docs/ARCHITECTURE.md` Section 1, "What Is Out of Scope":
   > - Email/nurture sequences (handled by campaign execution layers)

4. **No prompt templates for email.** No `.md`, `.txt`, `.json`, or `.yaml` file in the repo contains copy frameworks, methodology docs, or system prompts related to:
   - Cold email sequences
   - Josh Braun "poke the bear" methodology
   - Eric Nowoslawski archetypes
   - Persona-tier tone calibration (strategic/operational/technical)
   - No-pitch-in-email-1 rules
   - Observation + question CTAs
   - Tangible offer constraints

5. **No TODO comments or stubs for email.** Grep of the entire codebase for "email", "sequence", "nurture", "cold_email", "campaign_copy" returns zero results in code files.

6. **Pipeline registry has no email mapping.** The `GENERATOR_REGISTRY` in `src/pipeline/registry.py` contains 12 entries mapping `(artifact_type, surface)` to generator classes. None involve email.

### Adjacent content generation systems

The repo has extensive content generation for **non-email** channels:

| Generator | Content Type | Channels/Surfaces |
|---|---|---|
| AdCopyGenerator | Platform ad copy with char limits | LinkedIn, Meta, Google |
| AudioScriptGenerator | Voicemail/narration scripts | Voice channel |
| VideoScriptGenerator | Video ad scripts with timestamps | Meta, TikTok, Generic |
| PhysicalMailGenerator | Postcards and letters | Direct mail (for Lob) |
| LandingPageGenerator | Landing page content | Web (4 template types) |
| LeadMagnetGenerator | Long-form lead magnets | PDF (5 format types) |
| DocumentSlidesGenerator | Carousel/slide content | LinkedIn |
| CaseStudyGenerator | Case study narratives | Web (HTML) |
| ImageBriefGenerator | Image briefs for designers | Generic (JSON) |

The `AudioScriptGenerator` generates voicemail scripts (not email), and the `PhysicalMailGenerator` generates postcard/letter copy (not email). These are the closest to "outbound messaging" but are not cold email.

### Where might cold email generation live?

Based on the directive's context:
1. **campaign-engine-x** -- The directive mentions this was "scaffolded for multi-channel campaign content generation." This is the most likely home for cold email sequence generation, as the architecture doc explicitly says email/nurture sequences are "handled by campaign execution layers."
2. **outbound-engine-x-api** (OEX-API) -- Listed as a consumer of creative-engine-x in the architecture doc. OEX-API uses voicemail audio and direct mail postcards from creative-engine-x. Cold email logic may live here as well.
3. **Nowhere yet** -- The copy methodology (no pitch in email 1, observation + question CTA, tangible offer in email 2, persona-tier tone calibration) may exist only in conversation history and not be codified in any repo.

---

## Section 5: Markdown / Reference Files

### `docs/ARCHITECTURE.md` (1097 lines)

Core system architecture document. 13 sections covering:
- System overview (8 artifact types, 3 consumers, out-of-scope items)
- Core abstractions (artifact_type, surface, format_spec, subtypes)
- Routing model (two-level routing, route registry)
- Spec system (YAML config, hard/soft constraints, loading)
- Request/response contracts (GenerateRequest, sync/async responses, batch, webhooks)
- Plugin architecture (Generator -> Renderer -> Provider chain)
- Brand context system (by-reference + inline, 7 context types)
- Landing page hosting (/lp/{slug} serving, form submissions, analytics)
- Auth model (API keys, JWT, public routes, middleware chain)
- Storage architecture (Supabase Storage primary, S3 for video via Remotion Lambda)
- Async job system (artifact-type-based sync/async boundary)
- Infrastructure (full tech stack: FastAPI, Supabase, Railway, Doppler, Remotion, ElevenLabs, ReportLab, Jinja2)
- Design decisions (8 documented decisions with reasoning)

Full database schema and environment variables in appendices.

### `docs/POST_SHIP_ENGINEERING_AUDIT.md` (408 lines)

Post-ship audit from v0.1.0.0 release. Documents:
- 7 build phases, 41 Linear issues, 24,538 LOC, 420 tests
- Remediation priorities (P0: deployment fix, P1: integration testing)
- Phase breakdown: Foundation (13 tickets), Generators (10), Renderers (5), Voice (2), Video (5), Physical Mail (2), Hardening (8)

### `docs/FIGMA_API_REFERENCE.md` (1227 lines)

Complete Figma REST API reference covering 46 endpoints. Used as reference for the scaffold extraction system.

### `docs/FIGMA_EXTRACTION_REPORT.md` (582 lines)

Validation report for Figma scaffold zone extraction. 14 scaffolds validated, 94 checks. Documents zone detection, overlap analysis, and coverage metrics for each physical mail scaffold.

### `docs/FIGMA_IMPLEMENTATION_AUDIT.md` (357 lines)

Audit showing 0 of 46 Figma API endpoints have been built. This is a reference doc -- the Figma API is used only for scaffold extraction (offline), not at runtime.

### `docs/LOB_MAILER_CONSTRAINTS.md` (185 lines)

Physical dimension constraints for all Lob mailer types:
- Postcards: 4x6, 5x7, 6x9, 6x11 (front/back, safe zones, bleed)
- Letters: 8.5x11, 8.5x14 (inside letter + envelope)
- Self-mailers: 6x18 bifold, 11x9 bifold, 12x9 bifold, 17.75x9 trifold
- Booklet: 8.375x5.375 (cover + inside pages)
- Buckslip, card affix, snap pack (special formats)

### `docs/SCAFFOLD_MASTERS.md` (455 lines)

Physical mail template system documentation. 15 zone types (headline, body, CTA, logo, address, barcode, etc.). Zone hierarchy, margin rules, font size guidelines per format.

### `CHANGELOG.md` (19 lines)

```markdown
# Changelog

All notable changes to creative-engine-x-api will be documented in this file.

## [0.1.0.0] - 2026-03-26

### Added
- Foundation (CEX-5 through CEX-13): FastAPI scaffold, database schema (7 tables), API key auth
  with bcrypt, YAML spec system (13 specs), route registry, brand context service (7 context types),
  Claude AI client (dual model tiers), Supabase storage service, async job system with webhook delivery
- Generators (CEX-14 through CEX-23): Generator base class with protocol, ad copy (LinkedIn/Meta/Google),
  lead magnet (5 formats), landing page (4 templates), document slides (3 narrative patterns),
  video script, image brief, case study, audio script (NEW), physical mail (NEW -- postcards + letters)
- Renderers (CEX-24 through CEX-28): Renderer base protocol, PDF renderer (ReportLab), slide renderer
  (1:1 and 4:5), HTML renderer (Jinja2, 4 templates), landing page hosting router
- Voice (CEX-29 through CEX-30): ElevenLabs TTS provider with rate limit retries, audio renderer pipeline
- Video (CEX-31 through CEX-35): Remotion project scaffold (7 compositions), Lambda deployment scripts,
  Remotion Python provider (boto3), video renderer with progress polling, 5 shared composition components
- Physical Mail (CEX-36 through CEX-37): Provider protocol and adapter pattern, 14 Figma-validated
  scaffold types with Jinja2 HTML rendering
- Hardening (CEX-38 through CEX-45): Rate limiting, usage tracking, webhook reliability, structured errors,
  health checks, OpenAPI docs, Railway deployment config
- Pipeline orchestrator with full sync and async generation pipelines
- Pipeline registry mapping (artifact_type, surface) to generator/renderer classes
- Shared text utilities with word-boundary-aware truncation
- Integration tests for pipeline and routing
```

### Non-standard `.md` files checked

No other `.md` files exist in the repo beyond the 8 listed above, `CLAUDE.md`, and the context attachments. Specifically, there are **no** copy framework documents, methodology references, email writing guides, or prompt template markdown files.

### Prompt templates / framework files

- **No `/prompts/` directory** exists
- **No `/templates/` directory** with text/prompt templates (only HTML Jinja2 templates in `src/templates/`)
- **No `/skills/` directory** exists
- **No `/frameworks/` directory** exists
- **No `.txt` prompt template files** exist anywhere in the repo
- System prompts are embedded directly in Python generator classes (see Section 7)

---

## Section 6: LLM Integration Layer

### Claude Client (`src/integrations/claude_client.py`)

**Models:**
```python
MODEL_QUALITY = "claude-opus-4-20250514"
MODEL_FAST = "claude-sonnet-4-20250514"
```

**Data classes:**
```python
@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0

@dataclass
class GenerationResult:
    content: Any = None
    tool_results: list[dict] = field(default_factory=list)
    usage: TokenUsage = field(default_factory=TokenUsage)
    model: str = ""
    stop_reason: str = ""
```

**ClaudeClient class:**
- Constructor: `anthropic.AsyncAnthropic(api_key=api_key or settings.anthropic_api_key)`
- `generate(messages, system, model=MODEL_FAST, temperature=0.7, max_tokens=4096, tools=None, tool_choice=None, max_retries=3)`:
  - Exponential backoff on 429 (rate limit) and 500+ errors
  - Processes response: extracts text blocks or tool_use input
  - When tools are used, returns tool_use input as `content` (structured output via tool pattern)
  - Accumulates `TokenUsage` across retries

**API key management:** Via `settings.anthropic_api_key` from Doppler environment variable `ANTHROPIC_API_KEY`.

### Structured Output Pattern

All generators that need structured output use the Claude **tool_use pattern**:
1. Define a Pydantic `output_schema` on the generator class
2. `BaseGenerator.generate()` converts it to a tool definition: `tools=[{name: "produce_content", description: "...", input_schema: schema.model_json_schema()}]`
3. `tool_choice={type: "tool", name: "produce_content"}` forces Claude to respond with structured JSON matching the schema
4. Response parsing extracts the tool input as `GenerationResult.content`

This is **not** JSON mode -- it's the tool-use-for-structured-output pattern.

### Prompt Construction

All generators inherit from `BaseGenerator`, which provides:

**System prompt template** (from `build_system_prompt`):
```
You are an expert B2B content strategist creating {asset_label} content for {company}.

BRAND CONTEXT:
{brand_block}

TONE AND VOICE:
{brand_voice}

IMPORTANT RULES:
- All content must be specific to this company and audience -- never generic
- Use concrete examples, real numbers, and specific outcomes
- Match the brand voice consistently
- Focus on value to the reader, not features of the product
```

Where `brand_block` includes company name, industry, value proposition, competitor differentiators, and ICP definition. `asset_label` is derived from the spec description.

**User prompt template** (from `build_user_prompt`):
```
TARGET AUDIENCE:
{persona_block}

CAMPAIGN CONTEXT:
- Angle: {angle}
- Objective: {objective}
- Industry: {industry}

{asset_specific_instructions}

{social_proof_block}
```

Each generator subclass overrides `build_asset_specific_instructions()` to add generator-specific prompting (see Section 7).

---

## Section 7: Content Generators -- Full Inventory

### Generator Registry (`src/pipeline/registry.py`)

| (artifact_type, surface) | Generator Class | Model | Notes |
|---|---|---|---|
| `(structured_text, linkedin)` | AdCopyGenerator | Sonnet (fast) | LinkedIn ad copy |
| `(structured_text, meta)` | AdCopyGenerator | Sonnet (fast) | Meta ad copy |
| `(structured_text, google)` | AdCopyGenerator | Sonnet (fast) | Google RSA copy |
| `(structured_text, generic)` | ImageBriefGenerator | Sonnet (fast) | Default for generic |
| `(pdf, generic)` | LeadMagnetGenerator | Opus (quality) | Lead magnets |
| `(html_page, web)` | LandingPageGenerator | Opus (quality) | Landing pages |
| `(document_slides, linkedin)` | DocumentSlidesGenerator | Opus (quality) | Carousels |
| `(audio, voice_channel)` | AudioScriptGenerator | Sonnet (fast) | Voicemail scripts |
| `(video, generic)` | VideoScriptGenerator | Sonnet (fast) | Video scripts |
| `(video, meta)` | VideoScriptGenerator | Sonnet (fast) | Meta video scripts |
| `(video, tiktok)` | VideoScriptGenerator | Sonnet (fast) | TikTok video scripts |
| `(physical_mail, direct_mail)` | PhysicalMailGenerator | Sonnet (fast) | Postcards/letters |

**Subtype overrides:**
| (artifact_type, surface, subtype) | Generator |
|---|---|---|
| `(structured_text, generic, video_script)` | VideoScriptGenerator |
| `(structured_text, generic, image_brief)` | ImageBriefGenerator |
| `(html_page, web, case_study)` | CaseStudyGenerator |

### 1. AdCopyGenerator (`src/generators/ad_copy.py`)

**Type:** `ad_copy` | **Model:** Sonnet (fast) | **Temperature:** 0.7

**Platforms and output schemas:**

**LinkedIn:**
```python
class LinkedInAdCopyVariant(BaseModel):
    introductory_text: str  # Max 600 chars (150 before fold)
    headline: str           # Max 70 chars
    description: str        # Max 100 chars

class LinkedInAdCopyOutput(BaseModel):
    variants: list[LinkedInAdCopyVariant]  # Exactly 3
```

Prompt instructions: Generate 3 variants -- (1) problem-agitation, (2) social proof, (3) curiosity hook. Character limits enforced post-generation by `validate_ad_copy_limits()` which truncates at word boundaries.

**Meta:**
```python
class MetaAdCopyVariant(BaseModel):
    primary_text: str   # Max 125 chars
    headline: str       # Max 40 chars
    description: str    # Max 30 chars

class MetaAdCopyOutput(BaseModel):
    variants: list[MetaAdCopyVariant]  # Exactly 3
```

3 variants: outcome-focused, question hook, stat/proof.

**Google RSA:**
```python
class GoogleRSACopyOutput(BaseModel):
    headlines: list[str]     # 3-15 items, each max 30 chars
    descriptions: list[str]  # 2-4 items, each max 90 chars
    path1: str               # Max 15 chars
    path2: str               # Max 15 chars
```

10 headlines (30 chars each), 4 descriptions (90 chars each). Must include company name in at least 1 headline.

### 2. AudioScriptGenerator (`src/generators/audio_script.py`)

**Type:** `audio_script` | **Model:** Sonnet (fast) | **Temperature:** 0.5

```python
class AudioScriptOutput(BaseModel):
    script_text: str
    duration_seconds: int
    word_count: int
    cta_text: str
    tone_notes: str = ""
```

**Duration configs:** 15s (~38 words), 30s (~75 words), 60s (~150 words) at 150 WPM, 10% tolerance.

**Passthrough mode:** If `content_props["script_text"]` is provided, skips LLM generation and returns it directly with `model="passthrough"`.

**System prompt instructions:**
```
TASK: Generate a {duration}-second voicemail/narration script.
TARGET WORD COUNT: ~{word_target} words (+-10%)

SCRIPT REQUIREMENTS:
- Natural speech patterns -- use contractions, conversational tone
- Appropriate pauses indicated by commas and periods
- First-person singular preferred ('I wanted to reach out...')
- Single CTA per script -- avoid multiple asks
- No hard sell language in opening 5 seconds
- Script should sound natural when read aloud

STRUCTURE:
- Opening: Warm, personal greeting
- Body: Value statement
- CTA: One clear, specific action
- Closing: Brief, friendly sign-off
```

### 3. CaseStudyGenerator (`src/generators/case_study.py`)

**Type:** `case_study` | **Model:** Opus (quality) | **Temperature:** 0.6

```python
class CaseStudyNarrativeSection(BaseModel):
    heading: str
    body: str
    bullets: list[str] | None = None

class CaseStudyMetricOutput(BaseModel):
    value: str
    label: str

class CaseStudyContentOutput(BaseModel):
    headline: str
    sections: list[CaseStudyNarrativeSection]
    metrics: list[CaseStudyMetricOutput]
    quote_text: str | None = None
    quote_author: str | None = None
    quote_title: str | None = None
    cta_text: str = "Get Similar Results"
```

Sections: Situation, Challenge, Solution, Results -- each 200-400 words. 2-4 metrics with specific numbers. Third-person narrative. Quotes must not be fabricated.

### 4. DocumentSlidesGenerator (`src/generators/document_slides.py`)

**Type:** `document_slides` | **Model:** Opus (quality) | **Temperature:** 0.4

```python
class SlideOutput(BaseModel):
    headline: str           # Max 50 chars
    body: str | None        # Max 120 chars
    stat_callout: str | None
    stat_label: str | None
    is_cta_slide: bool = False
    cta_text: str | None = None

class DocumentSlidesOutput(BaseModel):
    slides: list[SlideOutput]   # 5-8 slides
    aspect_ratio: str = "1:1"
```

**3 narrative patterns:**
- `problem_solution`: Problem -> Agitate -> Bridge -> Evidence -> CTA
- `listicle`: Title -> Numbered tips/items -> CTA
- `data_story`: Hook stat -> Context -> Implications -> CTA

Validation: Truncates headlines >50 chars, body >120 chars. Forces last slide to CTA.

### 5. ImageBriefGenerator (`src/generators/image_brief.py`)

**Type:** `image_brief` | **Model:** Sonnet (fast) | **Temperature:** 0.6

```python
class ImageBriefOutput(BaseModel):
    concept_name: str
    intended_use: str
    dimensions: str
    visual_description: str
    text_overlay: str | None = None
    color_palette: list[str] = []   # Hex colors
    mood: str
    style_reference: str
    do_not_include: list[str] = []

class ImageBriefSetOutput(BaseModel):
    briefs: list[ImageBriefOutput]
```

**Platform dimensions:** linkedin_sponsored (1200x628), linkedin_carousel (1080x1080), meta_feed (1080x1080), meta_story (1080x1920), landing_page_hero (1920x1080).

**Anti-cliche guidance:** No handshake photos, generic offices, posed groups, holographic UIs, puzzle pieces.

### 6. LandingPageGenerator (`src/generators/landing_page.py`)

**Type:** `landing_page` | **Model:** Opus (quality) | **Temperature:** 0.5

4 template types selected by keyword matching on `objective + angle`:

| Template | Schema | Selection Keywords |
|---|---|---|
| `webinar` | `WebinarPageOutput` | webinar, event, workshop, summit, masterclass, live |
| `demo_request` | `DemoRequestPageOutput` | demo, trial, walkthrough, consultation |
| `case_study` | `CaseStudyPageOutput` | case study, success story, customer story |
| `lead_magnet_download` | `LeadMagnetPageOutput` | (default) |

```python
class LeadMagnetPageOutput(BaseModel):
    headline: str
    subhead: str
    value_props: list[str]
    cta_text: str = "Download Now"

class WebinarPageOutput(BaseModel):
    event_name: str
    headline: str
    agenda: list[str]
    cta_text: str = "Register Now"

class DemoRequestPageOutput(BaseModel):
    headline: str
    subhead: str
    benefits: list[LandingPageSectionOutput]
    cta_text: str = "Request Demo"

class CaseStudyPageOutput(BaseModel):
    customer_name: str
    headline: str
    sections: list[LandingPageSectionOutput]
    metrics: list[dict]
    quote_text: str | None = None
    quote_author: str | None = None
    quote_title: str | None = None
    cta_text: str = "Get Similar Results"
```

### 7. LeadMagnetGenerator (`src/generators/lead_magnet.py`)

**Type:** `lead_magnet` | **Model:** Opus (quality) | **Temperature:** 0.5

```python
class LeadMagnetSectionOutput(BaseModel):
    heading: str
    body: str
    bullets: list[str] = []
    callout_box: str | None = None

class LeadMagnetOutput(BaseModel):
    title: str
    subtitle: str
    sections: list[LeadMagnetSectionOutput]
```

**5 format types:**

| Format | Sections | Word Count |
|---|---|---|
| `checklist` | 4-6 categories, 15-25 items | 2,000-4,000 |
| `ultimate_guide` | 5 chapters | 5,500-8,500 |
| `benchmark_report` | Exec summary + 3-5 metrics + Recommendations | 4,000-8,000 |
| `template_toolkit` | Intro + 4-6 templates | 3,000-6,000 |
| `state_of_industry` | Exec summary + 4-6 findings + Implications | 6,000-10,000 |

**Two-pass generation:** For `ultimate_guide` and `state_of_industry` -- Pass 1 generates outline (temperature - 0.1), Pass 2 expands sections.

**Source content mode:** If `content_props["source_content"]` is set, injects up to 32K chars with instruction to restructure (not copy verbatim). If `source_url` is a YouTube URL, transcript is extracted automatically via pipeline preprocessing.

**Industry guidance:** SaaS, Healthcare, Financial Services, Manufacturing -- each with tone/language/CTA guidance baked into prompts.

**Format selection:** `select_lead_magnet_format(angle, objective, industry)` -- keyword scoring across all 5 formats.

### 8. PhysicalMailGenerator (`src/generators/physical_mail.py`)

**Type:** `physical_mail` | **Model:** Sonnet (fast) | **Temperature:** 0.4

```python
class PostcardOutput(BaseModel):
    headline: str       # Max 50 (4x6) or 60 (6x9) chars
    body_copy: str      # Max 200 (4x6) or 400 (6x9) chars
    cta_text: str
    subtype: str = "postcard_4x6"

class LetterOutput(BaseModel):
    salutation: str
    body_paragraphs: list[str]  # 2-3 paragraphs
    cta_text: str
    sign_off: str
    sender_name: str = ""

class PhysicalMailOutput(BaseModel):
    mail_type: str      # postcard_4x6, postcard_6x9, or letter
    postcard: PostcardOutput | None = None
    letter: LetterOutput | None = None
```

Subtypes: `postcard_4x6` (headline 50, body 200), `postcard_6x9` (headline 60, body 400), `letter` (250-400 words, 2-3 paragraphs). Validation truncates at word boundaries.

### 9. VideoScriptGenerator (`src/generators/video_script.py`)

**Type:** `video_script` | **Model:** Sonnet (fast) | **Temperature:** 0.5

```python
class ScriptSegment(BaseModel):
    timestamp_start: str
    timestamp_end: str
    spoken_text: str
    visual_direction: str
    text_overlay: str | None = None
    caption_text: str

class VideoScriptOutput(BaseModel):
    title: str
    duration: str
    aspect_ratio: str
    hook: ScriptSegment
    body: list[ScriptSegment]
    cta: ScriptSegment
    total_word_count: int
    music_direction: str
    target_platform: str
```

**Durations:** 30s (~75 words: Hook, Problem, Solution, CTA) and 60s (~150 words: Hook, Problem, Solution, Proof, CTA).

**Platform guidance:**
- LinkedIn: 4:5 portrait, professional, caption-heavy
- Meta: 4:5 feed / 9:16 reels, punchy/fast-paced
- YouTube: 16:9 landscape, educational, end screen CTA

---

## Section 8: Renderers / Output Formats

### Renderer Registry (`src/pipeline/registry.py`)

| (artifact_type, surface) | Renderer | Output |
|---|---|---|
| `(structured_text, *)` | None | JSON (inline in response) |
| `(pdf, generic)` | PDFRenderer | PDF binary |
| `(html_page, web)` | HTMLRenderer | HTML |
| `(document_slides, linkedin)` | SlideRenderer | PDF binary |
| `(audio, voice_channel)` | AudioRenderer | MP3 |
| `(video, *)` | VideoRenderer | MP4 |
| `(physical_mail, direct_mail)` | None | JSON (PDF rendering future via Lob) |

### PDFRenderer (`src/renderers/pdf_renderer.py`)

**Library:** ReportLab (Python, in-process)

**Output:** Lead magnet PDFs -- multi-page documents with:
- **Cover page:** Dark background (secondary color), primary color accent bar, company name top-left, centered title/subtitle in white
- **TOC page:** Numbered section headings
- **Content pages:** Section headings (secondary color, Helvetica-Bold 20pt), body (11pt), bullets, callout boxes with light primary background
- **Headers/footers:** Primary color line, company name, centered page numbers
- **Page size:** US Letter (8.5x11)

Brand context flows into colors (primary, secondary, accent), font family, company name, and logo URL.

### HTMLRenderer (`src/renderers/html_renderer.py`)

**Library:** Jinja2

**Templates:** 4 HTML templates in `src/templates/`:
- `lead_magnet_download.html` (152 lines) -- lead magnet download page
- `case_study.html` (162 lines) -- case study page
- `webinar.html` (155 lines) -- webinar registration page
- `demo_request.html` (164 lines) -- demo request page

Each template receives:
- Content data (from generator)
- `branding` dict: `primary_color` (default `#00e87b`), `secondary_color` (default `#09090b`), `font_family` (default `Inter, sans-serif`), `company_name`, `logo_url`
- `tracking` dict: `rudderstack_write_key`, `rudderstack_data_plane_url`

Templates include client-side RudderStack analytics (page views, form submissions, UTM capture).

### SlideRenderer (`src/renderers/slide_renderer.py`)

**Library:** ReportLab (Python, in-process)

PDF-based carousel slides:
- **Dimensions:** 1:1 -> 1080x1080px (540x540pt), 4:5 -> 1080x1350px (540x675pt)
- **Slide design:** Dark background (secondary color), primary accent bar at top, company name bottom-right, slide counter bottom-left
- **CTA slides:** Translucent primary accent circle center
- **Typography:** Headline 32pt white, body 16pt light gray, stat 72pt primary bold

### AudioRenderer (`src/renderers/audio_renderer.py`)

**Library:** ElevenLabs REST API (via `ElevenLabsProvider`)

**Provider details:**
- API: `POST /v1/text-to-speech/{voice_id}` with `xi-api-key` header
- Model: `eleven_multilingual_v2`
- Output: MP3 (44100Hz, 128kbps)
- Max characters: 5000
- Voice settings: stability=0.5, similarity_boost=0.75, style=0.15, speaker_boost=True
- Retry: Exponential backoff (1s base) on 429 and timeout, max 3 retries

**Pipeline:**
1. Generate script via `AudioScriptGenerator` (if no script_text provided)
2. Call ElevenLabs TTS
3. Upload MP3 to Supabase Storage

### VideoRenderer (`src/renderers/video_renderer.py`)

**Library:** Remotion Lambda (AWS) via `RemotionProvider`

**Provider details:**
- Triggers AWS Lambda function via `boto3.client("lambda").invoke()`
- Payload: `{type: "start", serveUrl, composition, codec: "h264", inputProps, framesPerLambda: 20}`
- Progress polling: `{type: "status", renderId, bucketName}` every 3 seconds
- Timeout: 300s default, 900s for long videos

**Composition map:**
```
meta_1x1      -> meta-ad-1x1
meta_9x16     -> meta-ad-9x16
meta_16x9     -> meta-ad-16x9
tiktok        -> tiktok-ad
generic_16x9  -> generic-video-16x9
generic_1x1   -> generic-video-1x1
generic_9x16  -> generic-video-9x16
```

**Pipeline:**
1. Generate video script via `VideoScriptGenerator` (if no scenes provided)
2. Extract scenes from script segments
3. Build Remotion inputProps (scenes, brand colors/logo/font, CTA text, music URL)
4. Trigger Lambda render
5. Poll progress (mapped to 0.3-0.8 range)
6. Download from S3, upload to Supabase Storage

### Physical Mail Rendering

Currently returns JSON only. No PDF rendering for physical mail yet. The architecture plans for Lob-compatible print-ready PDFs, but the `LobProvider` is not implemented. The `PhysicalMailGenerator` produces structured JSON that could be fed to Lob's API by a downstream consumer.

---

## Section 9: Database Schema

### Connection

- **asyncpg** connection pool (min=2, max=10) connected via `DATABASE_URL` (PostgreSQL on Supabase)
- Pool initialized on startup, closed on shutdown

### Tables (7)

#### `organizations`
```sql
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

#### `api_keys`
```sql
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
```

#### `brand_contexts`
```sql
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
```

#### `generated_artifacts`
```sql
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
```

#### `jobs`
```sql
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
```

#### `landing_page_submissions`
```sql
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
```

#### `usage_events`
```sql
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
```

### Tables for storing generated content

- **`generated_artifacts.content_json`** -- stores structured text output (ad copy, video scripts, image briefs) as JSONB
- **`generated_artifacts.content_url`** -- stores Supabase Storage URL for rendered artifacts (PDFs, HTML, audio, video)
- **`generated_artifacts.input_data`** -- stores full request input for replay/debugging
- **`generated_artifacts.brand_context_snapshot`** -- stores brand context used at generation time

There are **no** tables specifically for:
- Email templates or sequences
- Campaign copy
- Cold email content
- Prompt templates or copy frameworks

---

## Section 10: External Service Integrations

### 1. Anthropic/Claude

- **Client:** `anthropic.AsyncAnthropic` via `src/integrations/claude_client.py`
- **Models:** `claude-opus-4-20250514` (quality tier), `claude-sonnet-4-20250514` (fast tier)
- **Credentials:** `ANTHROPIC_API_KEY` env var via Doppler
- **Usage:** All content generation (9 generators). Tool-use pattern for structured output.
- **Rate limit handling:** Exponential backoff on 429, max 3 retries

### 2. Supabase

- **Database:** asyncpg connection pool to `DATABASE_URL` (Supabase PostgreSQL)
- **Storage:** `httpx.AsyncClient` to `{SUPABASE_URL}/storage/v1` via `src/integrations/supabase_client.py`
  - Bucket: `artifacts` (public, auto-created)
  - Path: `{org_id}/{artifact_type}/{artifact_id}.{ext}`
  - Operations: `ensure_bucket()`, `upload()`, `get_public_url()`
- **Credentials:** `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` via Doppler

### 3. ElevenLabs

- **Provider:** `src/providers/elevenlabs_provider.py`
- **API:** `POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}`
- **Model:** `eleven_multilingual_v2`
- **Output:** MP3 44100Hz 128kbps
- **Limits:** Max 5000 characters per request
- **Credentials:** `ELEVENLABS_API_KEY`, `ELEVENLABS_DEFAULT_VOICE_ID` via Doppler
- **Retry:** Exponential backoff on 429 and timeout, max 3 retries

### 4. AWS / Remotion Lambda

- **Provider:** `src/providers/remotion_provider.py`
- **Client:** `boto3.client("lambda")` via `asyncio.to_thread`
- **Operations:** Invoke Lambda with `type: "start"` (trigger render), `type: "status"` (poll progress)
- **Credentials:** `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION` via Doppler
- **Config:** `REMOTION_FUNCTION_NAME`, `REMOTION_SERVE_URL` via Doppler
- **Post-render:** Downloads from S3, uploads to Supabase Storage

### 5. RudderStack

- **Client:** `src/integrations/rudderstack.py`
- **API:** `POST {data_plane_url}/v1/identify`, `POST {data_plane_url}/v1/track`
- **Usage:** Server-side landing page analytics (form submissions)
- **Credentials:** `RUDDERSTACK_WRITE_KEY`, `RUDDERSTACK_DATA_PLANE_URL` via Doppler
- **Behavior:** Silently skips if not configured (optional)

### 6. Auth Engine (JWKS)

- **Client:** `PyJWKClient("https://api.authengine.dev/api/auth/jwks")`
- **Usage:** JWT validation for Bearer token auth
- **Algorithm:** EdDSA
- **Caching:** JWKS cache with 300s lifespan

### 7. Lob (NOT IMPLEMENTED)

- **Config:** `LOB_API_KEY` exists in Settings but is optional and unused
- **Status:** Architecture plans for Lob integration (print-ready PDF generation) but no provider code exists
- The `PhysicalMailGenerator` produces structured JSON that downstream consumers (OEX-API) would send to Lob

---

## Section 11: Configuration & Environment

### Environment Variables

| Variable | Required | Used By | Description |
|---|---|---|---|
| `DATABASE_URL` | Yes | `src/db.py` | PostgreSQL connection string (Supabase) |
| `SUPABASE_URL` | Yes | `src/integrations/supabase_client.py` | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | `src/integrations/supabase_client.py` | Supabase service role key |
| `ANTHROPIC_API_KEY` | Yes | `src/integrations/claude_client.py` | Claude API key |
| `AWS_ACCESS_KEY_ID` | Yes* | `src/providers/remotion_provider.py` | AWS credentials for Remotion Lambda |
| `AWS_SECRET_ACCESS_KEY` | Yes* | `src/providers/remotion_provider.py` | AWS credentials for Remotion Lambda |
| `AWS_REGION` | No | `src/providers/remotion_provider.py` | Default: `us-east-1` |
| `REMOTION_FUNCTION_NAME` | Yes* | `src/providers/remotion_provider.py` | Remotion Lambda function name |
| `REMOTION_SERVE_URL` | Yes* | `src/providers/remotion_provider.py` | Remotion Lambda site URL |
| `ELEVENLABS_API_KEY` | Yes* | `src/providers/elevenlabs_provider.py` | ElevenLabs API key |
| `ELEVENLABS_DEFAULT_VOICE_ID` | Yes* | `src/providers/elevenlabs_provider.py` | Default voice ID for TTS |
| `RUDDERSTACK_WRITE_KEY` | No | `src/integrations/rudderstack.py` | RudderStack analytics (optional) |
| `RUDDERSTACK_DATA_PLANE_URL` | No | `src/integrations/rudderstack.py` | RudderStack data plane URL |
| `API_KEY_SALT` | Yes | `src/config.py` | Salt for API key hashing |
| `LOB_API_KEY` | No | `src/config.py` | Lob API key (unused, future) |

\* Required only for video/audio artifact types.

### `.env.example`
```
# Secrets are managed via Doppler. Do not commit .env files.
```

### Doppler Configuration

No `.doppler.yaml` is committed (gitignored). Secrets are injected at runtime via `doppler run --` in the Dockerfile CMD. The project/config names are managed externally in Doppler.

---

## Section 12: CLAUDE.md / Agent Context Files

### `.claude/CLAUDE.md`

```markdown
## gstack
Use the /browse skill from gstack for all web browsing. Never use mcp__claude-in-chrome__* tools.
Available skills: /office-hours, /plan-ceo-review, /plan-eng-review, /plan-design-review,
/design-consultation, /review, /ship, /browse, /qa, /qa-only, /design-review,
/setup-browser-cookies, /retro, /investigate, /document-release, /codex, /careful, /freeze,
/guard, /unfreeze, /gstack-upgrade
```

This is a tool routing instruction for coding agents, not project documentation.

---

## Section 13: Dependencies

### `pyproject.toml`

```toml
[project]
name = "creative-engine-x-api"
version = "0.1.0"
description = "Creative asset pipeline service"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn>=0.34.0",
    "httpx>=0.28.0",
    "pydantic-settings>=2.7.0",
    "asyncpg>=0.30.0",
    "anthropic>=0.45.0",
    "PyJWT[crypto]>=2.8.0",
    "bcrypt>=4.2.0",
    "pyyaml>=6.0.0",
    "jinja2>=3.1.0",
    "reportlab>=4.1",
    "youtube-transcript-api>=1.0.0",
    "boto3>=1.35.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
```

**Notable dependencies:**
- `anthropic>=0.45.0` -- Claude API client
- `asyncpg>=0.30.0` -- Direct PostgreSQL driver (not SQLAlchemy/ORM)
- `reportlab>=4.1` -- In-process PDF generation
- `boto3>=1.35.0` -- AWS SDK for Remotion Lambda invocation
- `youtube-transcript-api>=1.0.0` -- YouTube transcript extraction for lead magnet source content
- `PyJWT[crypto]>=2.8.0` -- JWT validation with EdDSA support
- `bcrypt>=4.2.0` -- API key hashing

### Remotion Dependencies (`creative-engine-x-remotion/package.json`)

```json
{
  "name": "creative-engine-x-remotion",
  "dependencies": {
    "@remotion/bundler": "4.0.x",
    "@remotion/cli": "4.0.x",
    "@remotion/lambda": "4.0.x",
    "@remotion/renderer": "4.0.x",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "remotion": "4.0.x",
    "zod": "^3.22.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "typescript": "^5.3.0",
    "vitest": "^1.2.0"
  }
}
```

---

## Section 14: Gap Analysis -- What's Missing for Cold Email

### 1. What exists that directly supports cold email copy generation

**Nothing.** There is zero code, zero configuration, zero prompt templates, and zero data models in this repository that directly support cold email copy generation. The architecture doc explicitly excludes email sequences as out of scope.

### 2. What exists that could be adapted/extended for cold email

Several systems in creative-engine-x provide infrastructure that cold email generation could plug into:

| Existing System | How It Could Adapt | What's Needed |
|---|---|---|
| **BaseGenerator class** | Cold email generator would extend this. Gets brand context, persona, system prompt construction for free. | New `EmailSequenceGenerator` subclass |
| **Brand context system** | Already stores company_name, brand_voice, value_proposition, ICP, case_studies, testimonials, competitor_differentiators. All directly useful for email personalization. | Add email-specific fields (sender persona, company context for "poke the bear" observations) |
| **Spec system** | A new `structured_text__email.yaml` spec would define email constraints (word counts, step structure, tone rules). | New spec file |
| **Pipeline orchestrator** | Would route `(structured_text, email)` to the new generator. Existing sync pipeline handles structured text generation. | Registry entry |
| **ClaudeClient** | All LLM infrastructure (model selection, retries, structured output via tools) works as-is. | None -- ready to use |
| **AdCopyGenerator patterns** | Platform-specific output schemas, char limit validation, multi-variant generation. Email sequences would follow the same pattern with per-step schemas. | New output schemas |
| **AudioScriptGenerator** | "No hard sell in opening" rule, conversational tone, single CTA per script. These translate directly to cold email methodology. | Adapt constraints |

### 3. What is completely missing and would need to be built

**A. Email sequence generator** (`src/generators/email_sequence.py`)
- Pydantic output schema for multi-step email sequences
- Per-step constraints (word counts, CTA types, pitch rules)
- Persona-tier tone calibration (strategic, operational, technical)
- Copy methodology codified into system prompts:
  - No pitch in Email 1 (observation + question as CTA)
  - Tangible offer in Email 2
  - Josh Braun "poke the bear" methodology
  - Eric Nowoslawski archetype patterns

**B. Email spec file** (`src/specs/structured_text__email.yaml`)
- Sequence structure (3-5 steps)
- Per-step constraints (subject line char limits, body word counts, CTA types)
- Tone calibration rules per persona tier
- Timing guidance (day spacing between steps)

**C. Copy framework/methodology reference**
- Currently no `.md` or prompt template files codify the cold email methodology
- The rules from conversations (no-pitch-email-1, observation-question CTA, tangible-offer-email-2) need to be written into either:
  - A prompt template file (e.g., `src/generators/prompts/cold_email_methodology.md`)
  - Directly into the generator's system prompt

**D. Lead/prospect context model**
- The current `BrandContext` captures the sender's brand
- Cold email also needs the recipient context (lead's company, role, industry, signals, observations)
- Either extend `content_props` or add a `LeadContext` model

**E. Personalization engine**
- Per-lead customization (company-specific observations, role-specific pain points)
- Batch generation (one sequence per lead, N leads per request)
- Variable interpolation for merge fields

### 4. Where does cold email generation logic live?

Based on this audit:

| Location | Status |
|---|---|
| **creative-engine-x-api** | Does NOT contain cold email generation. Explicitly out of scope. |
| **campaign-engine-x** | Most likely home. Architecture doc says email sequences are "handled by campaign execution layers." Campaign-engine-x was scaffolded for multi-channel campaign content generation. |
| **outbound-engine-x-api (OEX-API)** | Possible home. Already consumes creative-engine-x for voicemail and direct mail. May contain or plan to contain email copy generation. |
| **chat-engine-x** | Possible. Could be involved in conversational email generation. |
| **Nowhere yet** | The cold email copy methodology (no-pitch-email-1, poke-the-bear, persona-tier calibration) may exist only in conversation history and design docs, not codified in any repo. |

### Architectural recommendation

The cleanest path depends on the desired ownership model:

**Option A: Add to creative-engine-x** (this repo)
- Pros: All content generation in one place. Reuses brand context, Claude client, structured output patterns, spec system.
- Cons: Architecture doc explicitly excludes email. Would need to update the scope decision.
- Work: New generator + spec + output schemas. ~1-2 days of implementation.

**Option B: Keep in campaign-engine-x**
- Pros: Respects the current scope boundary. Email sequences are campaign-execution-adjacent.
- Cons: Would need to either duplicate the generation infrastructure (Claude client, brand context, prompt patterns) or call creative-engine-x as a dependency.
- Work: Depends on campaign-engine-x's current state.

**Option C: Hybrid -- generate in creative-engine-x, orchestrate in campaign-engine-x**
- creative-engine-x gets a new `structured_text__email` spec that generates individual email steps
- campaign-engine-x orchestrates the full sequence (step ordering, per-lead personalization, send timing)
- This matches the existing pattern: creative-engine-x generates ad copy but doesn't post it to LinkedIn; it would generate email copy but not send it via the email platform.
