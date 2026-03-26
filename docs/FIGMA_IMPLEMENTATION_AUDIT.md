# Figma Implementation Audit

**Generated:** 2026-03-19
**Scope:** Complete audit of every Figma-related artifact in the `outbound-engine-x-api` codebase, plus gap analysis against the full Figma REST API surface (46 endpoints).

---

## Section 1: File Inventory

### Files with Content

| File Path | Description | Status |
|-----------|-------------|--------|
| `docs/api-reference-docs/figma/figma-embed-api/README.md` | Embed API documentation index — lists 3 source URLs and 3 content files | Has content |
| `docs/api-reference-docs/figma/figma-embed-api/embed-api.md` | Embed API documentation — message passing (5 types), events (7 types), code examples | Has content |
| `docs/api-reference-docs/figma/figma-embed-api/resources.md` | Embed resources — URL validation regex, supported file types, embed URL conversion, query parameters, node ID discovery, migration from Embed Kit 1.0 | Has content |
| `docs/api-reference-docs/figma/figma-embed-api/embed-files-prototypes.md` | Embed guide — supported content types, embedding flow, access control, customization, limitations | Has content |

### Empty Placeholder Files

49 empty markdown files exist across numbered subdirectories in `docs/api-reference-docs/figma/`. These are placeholder files from an uninitialized documentation submodule and contain no content.

<details>
<summary>Empty placeholder files (49 files)</summary>

| Directory | Files |
|-----------|-------|
| `00-general/` | `01-introduction.md`, `02-authentication.md`, `03-scopes.md`, `04-rate-limits.md` |
| `01-figma-files/` | `01-global-properties.md`, `02-node-types.md`, `03-property-types.md`, `endpoints/00-endpoints-overview.md` |
| `02-comments/` | `01-commenting-types.md`, `02-property-types.md`, `endpoints/00-endpoints-overview.md` |
| `03-users/` | `01-types.md`, `endpoints/00-endpoints-overview.md` |
| `04-version-history/` | `01-types.md`, `endpoints/00-endpoints-overview.md` |
| `05-projects/` | `01-types.md`, `endpoints/00-endpoints-overview.md` |
| `06-components/` | `01-types.md`, `endpoints/00-endpoints-overview.md` |
| `07-webhooks/` | `01-getting-started.md`, `02-events.md`, `03-types.md`, `05-security.md`, `endpoints/00-endpoints-overview.md` |
| `08-activity-logs/` | `01-getting-started.md`, `03-events.md`, `04-entity-types.md`, `05-action-types.md`, `endpoints/00-endpoints-overview.md` |
| `09-discovery/` | `01-getting-started.md`, `02-json-file-schema.md`, `03-text-types.md`, `endpoints/00-endpoints-overview.md` |
| `10-payments/` | `01-getting-started.md`, `02-types.md`, `endpoints/00-endpoints-overview.md` |
| `11-variables/` | `01-getting-started.md`, `02-types.md`, `endpoints/00-endpoints-overview.md`, `endpoints/01-get-local-variables.md`, `endpoints/02-get-published-variables.md`, `endpoints/03-post-variables.md` |
| `12-dev-resources/` | `01-getting-started.md`, `02-types.md`, `endpoints/00-endpoints-overview.md` |
| `13-library-analytics/` | `01-getting-started.md`, `endpoints/00-endpoints-overview.md` |
| Root | `14-errors.md`, `15-changelog.md` |

</details>

### External Reference Files (Not in Repo)

The authoritative Figma API reference materials are located outside this repository:
- `/Users/benjamincrane/api-reference-docs-new/figma/figma-openapi/openapi/openapi.yaml` — Official Figma REST API OpenAPI 3.1.0 specification (9,965 lines, 46 operations)
- `/Users/benjamincrane/api-reference-docs-new/figma/figma-openapi/dist/api_types.ts` — TypeScript type definitions generated from the OpenAPI spec (7,503 lines)
- `/Users/benjamincrane/api-reference-docs-new/figma/figma-openapi/README.md` — Repo overview, beta status, type naming conventions

---

## Section 2: Provider Functions

No Figma provider directory or functions exist anywhere in `src/providers/`.

The `src/providers/` directory contains the following provider subdirectories:
- `smartlead/` — Email campaigns (single-channel)
- `emailbison/` — Email campaigns + direct send
- `heyreach/` — LinkedIn outreach
- `lob/` — Direct mail (postcards, letters, self-mailers, checks)
- `voicedrop/` — Ringless voicemail
- `twilio/` — Voice, SMS, phone numbers, Trust Hub
- `llm/` — LLM provider abstraction (Anthropic)

No file in any provider directory references Figma. A full text search for "figma" (case-insensitive) across `src/` returned zero matches.

---

## Section 3: Router Endpoints

No Figma router endpoints exist anywhere in `src/routers/`.

The `src/routers/` directory contains 30 router files:

| Router | Purpose |
|--------|---------|
| `campaigns.py` | Email + multi-channel campaigns |
| `linkedin_campaigns.py` | LinkedIn campaigns (HeyReach) |
| `email_outreach.py` | EmailBison-specific bulk operations |
| `direct_mail.py` | Lob direct mail CRUD |
| `voicemail.py` | VoiceDrop endpoints |
| `phone_numbers.py` | Twilio phone number CRUD |
| `ivr.py` | Inbound IVR TwiML endpoints |
| `ivr_config.py` | IVR flow configuration |
| `outbound_calls.py` | Outbound call REST + TwiML |
| `sms.py` | SMS/MMS send endpoint |
| `voice.py` | Voice tokens, disposition, call actions |
| `twiml_apps.py` | TwiML Application CRUD |
| `trust_hub.py` | Trust Hub management + webhook |
| `twilio_webhooks.py` | Twilio webhook ingestion |
| `webhooks.py` | Webhook ingestion (all providers) |
| `orchestrator.py` | Internal orchestrator tick endpoint |
| `analytics.py` | Analytics dashboard endpoints |
| `organizations.py` | Organization CRUD |
| `companies.py` | Company CRUD |
| `users.py` | User CRUD |
| `entitlements.py` | Entitlement management |
| `auth_routes.py` | Authentication routes |
| `super_admin.py` | Super admin endpoints |
| `internal_provisioning.py` | Internal provisioning |
| `internal_reconciliation.py` | Internal reconciliation |
| `provisioning.py` | Company provisioning |
| `activity.py` | Activity timeline |
| `responses.py` | Response generation |
| `conversations.py` | Conversation management |
| `inboxes.py` | Inbox management |

None of these routers reference Figma in any capacity.

---

## Section 4: Pydantic Models

No Figma-related Pydantic models exist in `src/models/`.

The `src/models/` directory contains 26 model files covering campaigns, leads, multi-channel sequences, direct mail, LinkedIn, voice, SMS, IVR, trust hub, webhooks, analytics, organizations, companies, users, entitlements, auth, provisioning, reconciliation, email outreach, messages, inboxes, activity, conversations, responses, and sequences. None reference Figma.

---

## Section 5: Configuration & Environment Variables

No `FIGMA_*` environment variables exist in either `src/config.py` or `.env.example`.

**`src/config.py`** — Contains configuration for: database (Supabase), auth (JWT), Smartlead, HeyReach, EmailBison, Lob (17 variables), observability, internal scheduler. Zero Figma references.

**`.env.example`** — 36 lines covering database, Supabase, JWT, webhook secrets, Lob configuration (17 variables), observability, super admin seeding. Zero Figma references.

---

## Section 6: Orchestrator Integration

No Figma channel or provider mapping exists in the orchestrator.

**`src/orchestrator/step_executor.py`** — Routes multi-channel campaign steps to providers. Supported channels: `email` (EmailBison), `linkedin` (HeyReach), `direct_mail` (Lob), `voicemail` (VoiceDrop), `voice` (Twilio), `sms` (Twilio). No Figma channel or provider mapping.

**`src/orchestrator/event_bridge.py`** — Maps webhook provider slugs to campaign channels. Supported provider slugs: `smartlead`, `emailbison`, `heyreach`, `lob`, `voicedrop`, `twilio`. No Figma provider slug mapping.

---

## Section 7: Figma MCP Tools Inventory

The Figma MCP server is configured in the Cursor development environment at `/Users/benjamincrane/.cursor/projects/Users-benjamincrane-outbound-engine-x-api/mcps/user-figma/`. It provides 13 tools and 25 resource files.

### MCP Tools

| Tool Name | Description | Parameters | REST API Equivalent |
|-----------|-------------|------------|---------------------|
| `get_design_context` | Primary design-to-code tool — returns reference code, screenshot, and contextual metadata for a Figma node | `nodeId` (required), `fileKey` (required), `clientLanguages`, `clientFrameworks`, `forceCode`, `disableCodeConnect`, `excludeScreenshot` | Combines `GET /v1/files/{file_key}/nodes` + `GET /v1/images/{file_key}` — MCP enriches with code hints, Code Connect snippets, and design annotations |
| `get_screenshot` | Generate a screenshot for a given Figma node | `nodeId` (required), `fileKey` (required), `clientLanguages`, `clientFrameworks` | `GET /v1/images/{file_key}` — MCP adds desktop app integration |
| `get_metadata` | Get node/page metadata in XML format — structure overview with node IDs, layer types, names, positions, sizes | `nodeId` (required), `fileKey` (required), `clientLanguages`, `clientFrameworks` | `GET /v1/files/{file_key}/nodes` — MCP returns simplified XML instead of full JSON |
| `get_figjam` | Generate UI code for a FigJam node — only works for FigJam files | `nodeId` (required), `fileKey` (required), `clientLanguages`, `clientFrameworks`, `includeImagesOfNodes` | `GET /v1/files/{file_key}/nodes` — MCP-specific FigJam code generation |
| `get_variable_defs` | Get variable definitions (fonts, colors, sizes, spacings) for a given node | `nodeId` (required), `fileKey` (required), `clientLanguages`, `clientFrameworks` | `GET /v1/files/{file_key}/variables/local` — similar data, different format |
| `get_code_connect_map` | Get Code Connect mappings for a node — returns `{nodeId: {codeConnectSrc, codeConnectName}}` | `nodeId` (required), `fileKey` (required), `codeConnectLabel` | No direct REST API equivalent — Code Connect is a Figma platform feature managed via MCP |
| `get_code_connect_suggestions` | Get AI-suggested strategy for linking a Figma node to code components via Code Connect | `nodeId` (required), `fileKey` (required), `clientLanguages`, `clientFrameworks` | No REST API equivalent — MCP-exclusive AI capability |
| `add_code_connect_map` | Map a Figma node to a code component using Code Connect | `nodeId` (required), `fileKey` (required), `source` (required), `componentName` (required), `label` (required — enum of 15 frameworks), `template`, `templateDataJson`, `clientLanguages`, `clientFrameworks` | No direct REST API equivalent — Code Connect write operation |
| `send_code_connect_mappings` | Save multiple Code Connect mappings in bulk — use after `get_code_connect_suggestions` | `nodeId` (required), `fileKey` (required), `mappings` (required — array of `{nodeId, componentName, source, label, template, templateDataJson}`), `clientLanguages`, `clientFrameworks` | No direct REST API equivalent — bulk Code Connect write |
| `create_design_system_rules` | Provides a prompt to generate design system rules for the repository | `clientLanguages`, `clientFrameworks` | No REST API equivalent — MCP-exclusive AI capability |
| `generate_diagram` | Create FigJam diagrams from Mermaid.js syntax — supports flowcharts, sequence diagrams, state diagrams, gantt charts | `name` (required), `mermaidSyntax` (required), `userIntent` | No REST API equivalent — MCP-exclusive write-back capability |
| `generate_figma_design` | Capture/import a web page (by URL or HTML) into Figma | `captureId`, `fileName`, `planKey`, `outputMode` (enum: newFile, existingFile, clipboard), `fileKey`, `nodeId` | No REST API equivalent — MCP-exclusive web capture capability |
| `whoami` | Returns information about the authenticated Figma user | (none) | `GET /v1/me` — direct equivalent |

### MCP Resource Files

The Figma MCP server provides 25 resource files containing guidance and documentation:

| Resource | Purpose |
|----------|---------|
| `intro.json` | Server introduction and capabilities overview |
| `skill-implement-design.json` | Design-to-code implementation workflow guide |
| `skill-create-design-system-rules.json` | Design system rule creation guide |
| `skill-code-connect-components.json` | Code Connect component mapping guide |
| `code-connect-integration.json` | Code Connect integration details |
| `code-to-canvas.json` | Code-to-canvas workflow |
| `figjam-diagram-mcp-app.json` | FigJam diagram creation guide |
| `bringing-make-context-to-your-agent.json` | Figma Make context integration |
| `variables-vs-code.json` | Variables and code relationship |
| `structure-figma-file.json` | Figma file structure guidance |
| `write-effective-prompts.json` | Effective prompt writing for Figma MCP |
| `trigger-specific-tools.json` | Tool triggering guidance |
| `tools-and-prompts.json` | Tool and prompt reference |
| `add-custom-rules.json` | Custom rule configuration |
| `avoid-large-frames.json` | Performance guidance for large frames |
| `plans-access-and-permissions.json` | Plan access and permissions info |
| `local-server-installation.json` | Local MCP server installation |
| `remote-server-installation.json` | Remote MCP server installation |
| `mcp-clients-issues.json` | MCP client troubleshooting |
| `mcp-vs-agent.json` | MCP vs agent comparison |
| `tools-not-loading.json` | Tool loading troubleshooting |
| `server-returning-web-code.json` | Web code return troubleshooting |
| `images-stopped-loading.json` | Image loading troubleshooting |
| `getting-500-error.json` | 500 error troubleshooting |
| `stuck-or-slow.json` | Performance troubleshooting |

These resource files provide guidance and documentation only — they are not API endpoints.

---

## Section 8: Confirmed Non-Existent Locations

| Path | Status |
|------|--------|
| `app/` | **Does not exist** — this project uses `src/` |
| `app/contracts/` | **Does not exist** — no contracts directory in any form |
| `app/providers/` | **Does not exist** — providers are at `src/providers/` |
| `app/routers/execute_v1.py` | **Does not exist** — no operation ID registry pattern |
| `app/services/` | **Does not exist** — services are at `src/services/` |
| `trigger/src/` | **Does not exist** — Trigger.dev is an external service, no source code in this repo |
| `mcps/` (at repo root) | **Does not exist** — MCP tool descriptors are in Cursor's project config at `~/.cursor/projects/`, not in the repo |
| Any `FIGMA_*` env vars | **Do not exist** — zero Figma configuration in `src/config.py` or `.env.example` |
| Any Figma operation IDs wired in any router | **Do not exist** — zero Figma references in any router file |
| Any Figma MCP tools in the repo | **Do not exist** — MCP tools are in Cursor's project config, external to the repo |

---

## Section 9: Gap Analysis Table

Every endpoint in the Figma REST API (from the OpenAPI 3.1.0 specification, version 0.36.0), with implementation status in this codebase.

### Files

| Figma Endpoint | Method | Path | Operation ID | Our Function | Our Route | Status |
|---------------|--------|------|-------------|-------------|-----------|--------|
| Get file JSON | `GET` | `/v1/files/{file_key}` | `getFile` | — | — | Not Built |
| Get file nodes | `GET` | `/v1/files/{file_key}/nodes` | `getFileNodes` | — | — | Not Built |
| Render images | `GET` | `/v1/images/{file_key}` | `getImages` | — | — | Not Built |
| Get image fills | `GET` | `/v1/files/{file_key}/images` | `getImageFills` | — | — | Not Built |
| Get file metadata | `GET` | `/v1/files/{file_key}/meta` | `getFileMeta` | — | — | Not Built |

### Comments

| Figma Endpoint | Method | Path | Operation ID | Our Function | Our Route | Status |
|---------------|--------|------|-------------|-------------|-----------|--------|
| Get comments | `GET` | `/v1/files/{file_key}/comments` | `getComments` | — | — | Not Built |
| Post comment | `POST` | `/v1/files/{file_key}/comments` | `postComment` | — | — | Not Built |
| Delete comment | `DELETE` | `/v1/files/{file_key}/comments/{comment_id}` | `deleteComment` | — | — | Not Built |

### Comment Reactions

| Figma Endpoint | Method | Path | Operation ID | Our Function | Our Route | Status |
|---------------|--------|------|-------------|-------------|-----------|--------|
| Get reactions | `GET` | `/v1/files/{file_key}/comments/{comment_id}/reactions` | `getCommentReactions` | — | — | Not Built |
| Post reaction | `POST` | `/v1/files/{file_key}/comments/{comment_id}/reactions` | `postCommentReaction` | — | — | Not Built |
| Delete reaction | `DELETE` | `/v1/files/{file_key}/comments/{comment_id}/reactions` | `deleteCommentReaction` | — | — | Not Built |

### Users

| Figma Endpoint | Method | Path | Operation ID | Our Function | Our Route | Status |
|---------------|--------|------|-------------|-------------|-----------|--------|
| Get current user | `GET` | `/v1/me` | `getMe` | — | — | Not Built |

### Projects

| Figma Endpoint | Method | Path | Operation ID | Our Function | Our Route | Status |
|---------------|--------|------|-------------|-------------|-----------|--------|
| Get team projects | `GET` | `/v1/teams/{team_id}/projects` | `getTeamProjects` | — | — | Not Built |
| Get project files | `GET` | `/v1/projects/{project_id}/files` | `getProjectFiles` | — | — | Not Built |

### Version History

| Figma Endpoint | Method | Path | Operation ID | Our Function | Our Route | Status |
|---------------|--------|------|-------------|-------------|-----------|--------|
| Get file versions | `GET` | `/v1/files/{file_key}/versions` | `getFileVersions` | — | — | Not Built |

### Components

| Figma Endpoint | Method | Path | Operation ID | Our Function | Our Route | Status |
|---------------|--------|------|-------------|-------------|-----------|--------|
| Get team components | `GET` | `/v1/teams/{team_id}/components` | `getTeamComponents` | — | — | Not Built |
| Get file components | `GET` | `/v1/files/{file_key}/components` | `getFileComponents` | — | — | Not Built |
| Get component | `GET` | `/v1/components/{key}` | `getComponent` | — | — | Not Built |

### Component Sets

| Figma Endpoint | Method | Path | Operation ID | Our Function | Our Route | Status |
|---------------|--------|------|-------------|-------------|-----------|--------|
| Get team component sets | `GET` | `/v1/teams/{team_id}/component_sets` | `getTeamComponentSets` | — | — | Not Built |
| Get file component sets | `GET` | `/v1/files/{file_key}/component_sets` | `getFileComponentSets` | — | — | Not Built |
| Get component set | `GET` | `/v1/component_sets/{key}` | `getComponentSet` | — | — | Not Built |

### Styles

| Figma Endpoint | Method | Path | Operation ID | Our Function | Our Route | Status |
|---------------|--------|------|-------------|-------------|-----------|--------|
| Get team styles | `GET` | `/v1/teams/{team_id}/styles` | `getTeamStyles` | — | — | Not Built |
| Get file styles | `GET` | `/v1/files/{file_key}/styles` | `getFileStyles` | — | — | Not Built |
| Get style | `GET` | `/v1/styles/{key}` | `getStyle` | — | — | Not Built |

### Webhooks

| Figma Endpoint | Method | Path | Operation ID | Our Function | Our Route | Status |
|---------------|--------|------|-------------|-------------|-----------|--------|
| Get webhooks | `GET` | `/v2/webhooks` | `getWebhooks` | — | — | Not Built |
| Create webhook | `POST` | `/v2/webhooks` | `postWebhook` | — | — | Not Built |
| Get webhook | `GET` | `/v2/webhooks/{webhook_id}` | `getWebhook` | — | — | Not Built |
| Update webhook | `PUT` | `/v2/webhooks/{webhook_id}` | `putWebhook` | — | — | Not Built |
| Delete webhook | `DELETE` | `/v2/webhooks/{webhook_id}` | `deleteWebhook` | — | — | Not Built |
| Get team webhooks | `GET` | `/v2/teams/{team_id}/webhooks` | `getTeamWebhooks` | — | — | Not Built |
| Get webhook requests | `GET` | `/v2/webhooks/{webhook_id}/requests` | `getWebhookRequests` | — | — | Not Built |

### Activity Logs

| Figma Endpoint | Method | Path | Operation ID | Our Function | Our Route | Status |
|---------------|--------|------|-------------|-------------|-----------|--------|
| Get activity logs | `GET` | `/v1/activity_logs` | `getActivityLogs` | — | — | Not Built |

### Payments

| Figma Endpoint | Method | Path | Operation ID | Our Function | Our Route | Status |
|---------------|--------|------|-------------|-------------|-----------|--------|
| Get payments | `GET` | `/v1/payments` | `getPayments` | — | — | Not Built |

### Variables

| Figma Endpoint | Method | Path | Operation ID | Our Function | Our Route | Status |
|---------------|--------|------|-------------|-------------|-----------|--------|
| Get local variables | `GET` | `/v1/files/{file_key}/variables/local` | `getLocalVariables` | — | — | Not Built |
| Get published variables | `GET` | `/v1/files/{file_key}/variables/published` | `getPublishedVariables` | — | — | Not Built |
| Create/modify/delete variables | `POST` | `/v1/files/{file_key}/variables` | `postVariables` | — | — | Not Built |

### Dev Resources

| Figma Endpoint | Method | Path | Operation ID | Our Function | Our Route | Status |
|---------------|--------|------|-------------|-------------|-----------|--------|
| Get dev resources | `GET` | `/v1/files/{file_key}/dev_resources` | `getDevResources` | — | — | Not Built |
| Create dev resources | `POST` | `/v1/dev_resources` | `postDevResources` | — | — | Not Built |
| Update dev resources | `PUT` | `/v1/dev_resources` | `putDevResources` | — | — | Not Built |
| Delete dev resource | `DELETE` | `/v1/files/{file_key}/dev_resources/{dev_resource_id}` | `deleteDevResource` | — | — | Not Built |

### Library Analytics

| Figma Endpoint | Method | Path | Operation ID | Our Function | Our Route | Status |
|---------------|--------|------|-------------|-------------|-----------|--------|
| Component actions | `GET` | `/v1/analytics/libraries/{file_key}/component/actions` | `getLibraryAnalyticsComponentActions` | — | — | Not Built |
| Component usages | `GET` | `/v1/analytics/libraries/{file_key}/component/usages` | `getLibraryAnalyticsComponentUsages` | — | — | Not Built |
| Style actions | `GET` | `/v1/analytics/libraries/{file_key}/style/actions` | `getLibraryAnalyticsStyleActions` | — | — | Not Built |
| Style usages | `GET` | `/v1/analytics/libraries/{file_key}/style/usages` | `getLibraryAnalyticsStyleUsages` | — | — | Not Built |
| Variable actions | `GET` | `/v1/analytics/libraries/{file_key}/variable/actions` | `getLibraryAnalyticsVariableActions` | — | — | Not Built |
| Variable usages | `GET` | `/v1/analytics/libraries/{file_key}/variable/usages` | `getLibraryAnalyticsVariableUsages` | — | — | Not Built |

---

### Summary

```
Total Figma REST API endpoints: 46
Built:      0
Partial:    0
Not Built: 46

Figma MCP tools available:            13
MCP tools with REST API equivalents:   4  (get_design_context, get_screenshot, get_variable_defs, whoami)
MCP-exclusive tools:                   9  (get_metadata enrichment, get_figjam, get_code_connect_map, get_code_connect_suggestions, add_code_connect_map, send_code_connect_mappings, create_design_system_rules, generate_diagram, generate_figma_design)
```
