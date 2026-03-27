# Changelog

All notable changes to creative-engine-x-api will be documented in this file.

## [0.1.0.0] - 2026-03-26

### Added
- **Foundation (CEX-5 through CEX-13):** FastAPI scaffold, database schema (7 tables), API key auth with bcrypt, YAML spec system (13 specs), route registry, brand context service (7 context types), Claude AI client (dual model tiers), Supabase storage service, async job system with webhook delivery
- **Generators (CEX-14 through CEX-23):** Generator base class with protocol, ad copy (LinkedIn/Meta/Google), lead magnet (5 formats), landing page (4 templates), document slides (3 narrative patterns), video script, image brief, case study, audio script (NEW), physical mail (NEW — postcards + letters)
- **Renderers (CEX-24 through CEX-28):** Renderer base protocol, PDF renderer (ReportLab), slide renderer (1:1 and 4:5), HTML renderer (Jinja2, 4 templates), landing page hosting router
- **Voice (CEX-29 through CEX-30):** ElevenLabs TTS provider with rate limit retries, audio renderer pipeline
- **Video (CEX-31 through CEX-35):** Remotion project scaffold (7 compositions), Lambda deployment scripts, Remotion Python provider (boto3), video renderer with progress polling, 5 shared composition components
- **Physical Mail (CEX-36 through CEX-37):** Provider protocol and adapter pattern, 14 Figma-validated scaffold types with Jinja2 HTML rendering
- **Hardening (CEX-38 through CEX-45):** Provider adapter registry, rate limiting (sliding window, 60rpm), usage tracking with /usage endpoint, webhook reliability (3 retries, HMAC-SHA256), structured error handling (7 types), health checks (/health/ready + /health/live), OpenAPI docs, Railway deployment config
- **Pipeline orchestrator:** Full sync and async generation pipelines wired to /generate endpoint (generator → renderer → storage → DB)
- **Pipeline registry:** Maps (artifact_type, surface) tuples to generator/renderer classes with subtype overrides
- **Shared text utilities:** Word-boundary-aware truncation used consistently across all generators
- **Integration tests:** Pipeline registry, sync/async orchestrator, and text utility tests
