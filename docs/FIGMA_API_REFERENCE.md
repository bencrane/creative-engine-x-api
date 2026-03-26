# Figma API Reference

**Generated:** 2026-03-19
**Source:** Synthesized from the Figma REST API OpenAPI 3.1.0 specification (version 0.36.0, 46 operations), Embed API documentation (4 files), and TypeScript type definitions (7,503 lines).
**Companion:** See `docs/FIGMA_IMPLEMENTATION_AUDIT.md` for OEX implementation status and gap analysis.

---

## Section 1: Overview

The Figma REST API provides programmatic access to Figma files, projects, components, styles, comments, webhooks, variables, design tokens, export capabilities, and library analytics. It enables reading design file structures, rendering nodes as images (PNG, JPG, SVG, PDF), managing comments and reactions, subscribing to file change events via webhooks, reading and writing design variables/tokens, linking dev resources to design nodes, and querying library usage analytics.

The Figma Embed API enables embedding live Figma designs and prototypes in web applications via iframe with bidirectional message-passing control. It supports navigating prototypes, changing component states, and receiving events for user interactions.

**API Base URL:** `https://api.figma.com`

**API Version:** 0.36.0 (OpenAPI 3.1.0, beta)

**Key characteristics:**
- The API is read-heavy — most endpoints retrieve design data. Write operations exist for comments, comment reactions, webhooks, variables, and dev resources.
- Webhook endpoints use `/v2/` while all other endpoints use `/v1/`.
- Variables endpoints require Enterprise plan membership.
- Image export URLs are temporary (expire after 30 days for rendered images, 14 days for image fills).

---

## Section 2: Authentication

### Personal Access Tokens

Personal access tokens authenticate requests from server-side integrations, scripts, and CI/CD pipelines.

- **How to obtain:** Generated from Figma account settings (Settings → Personal Access Tokens)
- **Header format:** `X-FIGMA-TOKEN: {token}`
- **Scope:** Full access to all endpoints the user has permission for
- **When to use:** Server-side integrations, automated pipelines, OEX provider adapter

### OAuth 2.0

OAuth 2.0 provides delegated access for user-facing applications.

- **Authorization URL:** `https://www.figma.com/oauth`
- **Token URL:** `https://api.figma.com/v1/oauth/token`
- **Refresh URL:** `https://api.figma.com/v1/oauth/refresh`
- **Flow:** Authorization Code

**Scopes:**

| Scope | Description | Used By |
|-------|-------------|---------|
| `current_user:read` | Read name, email, and profile image | `getMe` |
| `file_content:read` | Read file contents (nodes, editor type) | `getFile`, `getFileNodes`, `getImages`, `getImageFills` |
| `file_metadata:read` | Read file metadata | `getFileMeta` |
| `file_comments:read` | Read file comments | `getComments`, `getCommentReactions` |
| `file_comments:write` | Post/delete comments and reactions | `postComment`, `deleteComment`, `postCommentReaction`, `deleteCommentReaction` |
| `file_versions:read` | Read file version history | `getFileVersions` |
| `file_variables:read` | Read variables (Enterprise only) | `getLocalVariables`, `getPublishedVariables` |
| `file_variables:write` | Write variables (Enterprise only) | `postVariables` |
| `file_dev_resources:read` | Read dev resources | `getDevResources` |
| `file_dev_resources:write` | Write dev resources | `postDevResources`, `putDevResources`, `deleteDevResource` |
| `files:read` | **Deprecated.** Read files, projects, users, versions, comments, components, styles, webhooks | Most read endpoints (legacy) |
| `projects:read` | List projects and files in projects | `getTeamProjects`, `getProjectFiles` |
| `library_content:read` | Read published components/styles of files | `getFileComponents`, `getFileComponentSets`, `getFileStyles` |
| `library_assets:read` | Read individual published components/styles | `getComponent`, `getComponentSet`, `getStyle` |
| `team_library_content:read` | Read published components/styles of teams | `getTeamComponents`, `getTeamComponentSets`, `getTeamStyles` |
| `library_analytics:read` | Read library analytics data | All 6 library analytics endpoints |
| `webhooks:read` | Read webhook metadata | `getWebhooks`, `getWebhook`, `getTeamWebhooks`, `getWebhookRequests` |
| `webhooks:write` | Create and manage webhooks | `postWebhook`, `putWebhook`, `deleteWebhook` |

**Organization-level OAuth:**

| Scope | Description | Used By |
|-------|-------------|---------|
| `org:activity_log_read` | Read organization activity logs | `getActivityLogs` |

---

## Section 3: Endpoint Reference by Resource

### 3a. Files — 5 endpoints

**Implementation status:** Not Built — no provider functions, routes, or models exist for this resource. See gap analysis in `docs/FIGMA_IMPLEMENTATION_AUDIT.md`.

#### Get file JSON

- **`GET /v1/files/{file_key}`**
- **Operation ID:** `getFile`
- **Purpose:** Returns the full document JSON for a Figma file, including all nodes, components metadata, and styles.
- **Security:** `PersonalAccessToken` or `OAuth2` (`file_content:read` or `files:read`)
- **Path parameters:**
  - `file_key` (string, required) — File key or branch key. Parsed from `https://www.figma.com/file/{file_key}/{title}`.
- **Query parameters:**
  - `version` (string) — Specific version ID. Omit for current version.
  - `ids` (string) — Comma-separated node IDs to return a subset of the document. Ancestor chains and dependencies are included.
  - `depth` (number) — Tree traversal depth. 1 = Pages only, 2 = Pages + top-level objects. Omit for full tree.
  - `geometry` (string) — Set to `"paths"` to export vector data.
  - `plugin_data` (string) — Comma-separated plugin IDs and/or `"shared"` to include plugin data.
  - `branch_data` (boolean, default `false`) — Include branch metadata in response.
- **Response:** `GetFileResponse` — `document` (DOCUMENT node), `components` (map of node ID → component metadata), `schemaVersion`, `styles` (map of style ID → style metadata), `name`, `lastModified`, `thumbnailUrl`, `version`, `editorType`, `linkAccess`.
- **Errors:** 400, 403, 404, 429, 500

#### Get file nodes

- **`GET /v1/files/{file_key}/nodes`**
- **Operation ID:** `getFileNodes`
- **Purpose:** Returns specific nodes by ID from a file, without fetching the entire document.
- **Security:** `PersonalAccessToken` or `OAuth2` (`file_content:read` or `files:read`)
- **Path parameters:**
  - `file_key` (string, required) — File key or branch key.
- **Query parameters:**
  - `ids` (string, required) — Comma-separated node IDs to retrieve.
  - `version` (string) — Specific version ID.
  - `depth` (number) — Traversal depth counted from the desired node (not document root).
  - `geometry` (string) — Set to `"paths"` for vector data.
  - `plugin_data` (string) — Plugin IDs to include plugin data.
- **Response:** `GetFileNodesResponse` — `nodes` (map of node ID → node JSON, values may be `null` if node doesn't exist), `name`, `lastModified`, `thumbnailUrl`, `version`, `editorType`, `linkAccess`.
- **Errors:** 400, 403, 404, 429, 500

#### Render images

- **`GET /v1/images/{file_key}`**
- **Operation ID:** `getImages`
- **Purpose:** Renders file nodes as images. Returns a map of node IDs to temporary download URLs.
- **Security:** `PersonalAccessToken` or `OAuth2` (`file_content:read` or `files:read`)
- **Path parameters:**
  - `file_key` (string, required) — File key or branch key.
- **Query parameters:**
  - `ids` (string, required) — Comma-separated node IDs to render.
  - `version` (string) — Specific version ID.
  - `scale` (number, 0.01–4) — Image scaling factor.
  - `format` (string, enum: `jpg`, `png`, `svg`, `pdf`, default `png`) — Output format.
  - `svg_outline_text` (boolean, default `true`) — Render text as outlines in SVG (guarantees visual accuracy but text is not selectable).
  - `svg_include_id` (boolean, default `false`) — Add layer name to SVG element `id` attribute.
  - `svg_include_node_id` (boolean, default `false`) — Add node ID to SVG `data-node-id` attribute.
  - `svg_simplify_stroke` (boolean, default `true`) — Simplify strokes instead of using `<mask>`.
  - `contents_only` (boolean, default `true`) — Exclude overlapping content from rendering.
  - `use_absolute_bounds` (boolean, default `false`) — Use full node dimensions (useful for text nodes).
- **Response:** `GetImagesResponse` — `images` (map of node ID → URL or `null` if render failed). URLs expire after 30 days. Max 32 megapixels per image.
- **Errors:** 400, 403, 404, 429, 500

#### Get image fills

- **`GET /v1/files/{file_key}/images`**
- **Operation ID:** `getImageFills`
- **Purpose:** Returns download URLs for all user-supplied images in a file (image fills in Paint objects).
- **Security:** `PersonalAccessToken` or `OAuth2` (`file_content:read` or `files:read`)
- **Path parameters:**
  - `file_key` (string, required) — File key or branch key.
- **Response:** `GetImageFillsResponse` — `images` (map of image reference → download URL). URLs expire after 14 days. Image references are found in `imageRef` attributes from the GET files endpoint.
- **Errors:** 400, 403, 404, 429, 500

#### Get file metadata

- **`GET /v1/files/{file_key}/meta`**
- **Operation ID:** `getFileMeta`
- **Purpose:** Lightweight file metadata without the full document tree.
- **Security:** `PersonalAccessToken` or `OAuth2` (`file_metadata:read` or `files:read`)
- **Path parameters:**
  - `file_key` (string, required) — File key or branch key.
- **Response:** `GetFileMetaResponse` — File name, last modified, thumbnail URL, version, editor type, and link access without the document node tree.
- **Errors:** 400, 403, 404, 429, 500

### 3b. Comments — 3 endpoints

**Implementation status:** Not Built — no provider functions, routes, or models exist for this resource. See gap analysis in `docs/FIGMA_IMPLEMENTATION_AUDIT.md`.

#### Get comments

- **`GET /v1/files/{file_key}/comments`**
- **Operation ID:** `getComments`
- **Purpose:** Get all comments on a file.
- **Security:** `PersonalAccessToken` or `OAuth2` (`file_comments:read` or `files:read`)
- **Path parameters:**
  - `file_key` (string, required) — File key or branch key.
- **Query parameters:**
  - `as_md` (boolean) — Return comments as markdown equivalents when applicable.
- **Response:** `GetCommentsResponse` — Array of comment objects with `id`, `message`, `file_key`, `parent_id`, `user`, `created_at`, `resolved_at`, `client_meta` (position), `order_id`.
- **Errors:** 403, 404, 429, 500

#### Post comment

- **`POST /v1/files/{file_key}/comments`**
- **Operation ID:** `postComment`
- **Purpose:** Post a new comment on a file.
- **Security:** `PersonalAccessToken` or `OAuth2` (`file_comments:write`)
- **Path parameters:**
  - `file_key` (string, required) — File key or branch key.
- **Request body:**
  - `message` (string, required) — Comment text.
  - `comment_id` (string) — ID of root comment to reply to (cannot reply to replies).
  - `client_meta` — Position: `Vector` (x,y), `FrameOffset` (node_id + node_offset), `Region`, or `FrameOffsetRegion`.
- **Response:** `PostCommentResponse` — Created comment object.
- **Errors:** 400, 403, 404, 429, 500

#### Delete comment

- **`DELETE /v1/files/{file_key}/comments/{comment_id}`**
- **Operation ID:** `deleteComment`
- **Purpose:** Delete a comment. Only the comment author can delete it.
- **Security:** `PersonalAccessToken` or `OAuth2` (`file_comments:write`)
- **Path parameters:**
  - `file_key` (string, required), `comment_id` (string, required)
- **Response:** `DeleteCommentResponse`
- **Errors:** 403, 404, 429, 500

### 3c. Comment Reactions — 3 endpoints

**Implementation status:** Not Built — no provider functions, routes, or models exist for this resource. See gap analysis in `docs/FIGMA_IMPLEMENTATION_AUDIT.md`.

#### Get comment reactions

- **`GET /v1/files/{file_key}/comments/{comment_id}/reactions`**
- **Operation ID:** `getCommentReactions`
- **Purpose:** Get paginated list of reactions on a comment.
- **Security:** `PersonalAccessToken` or `OAuth2` (`file_comments:read` or `files:read`)
- **Path parameters:**
  - `file_key` (string, required), `comment_id` (string, required)
- **Query parameters:**
  - `cursor` (string) — Pagination cursor from previous response.
- **Response:** `GetCommentReactionsResponse` — Array of reaction objects with user and emoji data.
- **Errors:** 403, 404, 429, 500

#### Post comment reaction

- **`POST /v1/files/{file_key}/comments/{comment_id}/reactions`**
- **Operation ID:** `postCommentReaction`
- **Purpose:** Add a reaction to a comment.
- **Security:** `PersonalAccessToken` or `OAuth2` (`file_comments:write`)
- **Request body:**
  - `emoji` (Emoji, required) — The emoji to react with.
- **Response:** `PostCommentReactionResponse`
- **Errors:** 400, 403, 404, 429, 500

#### Delete comment reaction

- **`DELETE /v1/files/{file_key}/comments/{comment_id}/reactions`**
- **Operation ID:** `deleteCommentReaction`
- **Purpose:** Delete a reaction. Only the reaction author can delete it.
- **Security:** `PersonalAccessToken` or `OAuth2` (`file_comments:write`)
- **Query parameters:**
  - `emoji` (Emoji, required) — The emoji reaction to remove.
- **Response:** `DeleteCommentReactionResponse`
- **Errors:** 403, 404, 429, 500

### 3d. Users — 1 endpoint

**Implementation status:** Not Built — no provider functions, routes, or models exist for this resource. See gap analysis in `docs/FIGMA_IMPLEMENTATION_AUDIT.md`.

#### Get current user

- **`GET /v1/me`**
- **Operation ID:** `getMe`
- **Purpose:** Returns info about the currently authenticated user.
- **Security:** `PersonalAccessToken` or `OAuth2` (`current_user:read` or `files:read`)
- **Response:** `GetMeResponse` — `id`, `email`, `handle`, `img_url`.
- **Errors:** 403, 429, 500

### 3e. Projects — 2 endpoints

**Implementation status:** Not Built — no provider functions, routes, or models exist for this resource. See gap analysis in `docs/FIGMA_IMPLEMENTATION_AUDIT.md`.

#### Get team projects

- **`GET /v1/teams/{team_id}/projects`**
- **Operation ID:** `getTeamProjects`
- **Purpose:** List all projects within a team (only projects visible to the authenticated user).
- **Security:** `PersonalAccessToken` or `OAuth2` (`projects:read` or `files:read`)
- **Path parameters:**
  - `team_id` (string, required) — Team ID (found in team page URL).
- **Response:** `GetTeamProjectsResponse` — `name` (team name), `projects` (array of `{id, name}`).
- **Errors:** 400, 403, 429, 500

#### Get project files

- **`GET /v1/projects/{project_id}/files`**
- **Operation ID:** `getProjectFiles`
- **Purpose:** List all files within a project.
- **Security:** `PersonalAccessToken` or `OAuth2` (`projects:read` or `files:read`)
- **Path parameters:**
  - `project_id` (string, required)
- **Query parameters:**
  - `branch_data` (boolean, default `false`) — Include branch metadata for each main file.
- **Response:** `GetProjectFilesResponse` — `name` (project name), `files` (array of file metadata objects).
- **Errors:** 400, 403, 429, 500

### 3f. Version History — 1 endpoint

**Implementation status:** Not Built — no provider functions, routes, or models exist for this resource. See gap analysis in `docs/FIGMA_IMPLEMENTATION_AUDIT.md`.

#### Get file versions

- **`GET /v1/files/{file_key}/versions`**
- **Operation ID:** `getFileVersions`
- **Purpose:** Fetch version history of a file. Use version IDs with other endpoints to access specific versions.
- **Security:** `PersonalAccessToken` or `OAuth2` (`file_versions:read` or `files:read`)
- **Path parameters:**
  - `file_key` (string, required) — File key or branch key.
- **Query parameters:**
  - `page_size` (number, max 50, default 30) — Items per page.
  - `before` (number) — Version ID to paginate before (get older versions).
  - `after` (number) — Version ID to paginate after (get newer versions).
- **Response:** `GetFileVersionsResponse` — `versions` (array of `{id, created_at, label, description, user}`) with pagination.
- **Errors:** 403, 404, 429, 500

### 3g. Components — 3 endpoints

**Implementation status:** Not Built — no provider functions, routes, or models exist for this resource. See gap analysis in `docs/FIGMA_IMPLEMENTATION_AUDIT.md`.

#### Get team components

- **`GET /v1/teams/{team_id}/components`**
- **Operation ID:** `getTeamComponents`
- **Purpose:** Get paginated list of published components within a team library.
- **Security:** `PersonalAccessToken` or `OAuth2` (`team_library_content:read` or `files:read`)
- **Path parameters:**
  - `team_id` (string, required)
- **Query parameters:**
  - `page_size` (number, default 30, max 1000) — Items per page.
  - `after` (number) — Cursor to start retrieving after (exclusive with `before`).
  - `before` (number) — Cursor to start retrieving before (exclusive with `after`).
- **Response:** `GetTeamComponentsResponse` — Paginated component metadata with `key`, `file_key`, `node_id`, `thumbnail_url`, `name`, `description`, `containing_frame`, `user`.
- **Errors:** 400, 403, 404, 429, 500

#### Get file components

- **`GET /v1/files/{file_key}/components`**
- **Operation ID:** `getFileComponents`
- **Purpose:** Get published components within a file library.
- **Security:** `PersonalAccessToken` or `OAuth2` (`library_content:read` or `files:read`)
- **Path parameters:**
  - `file_key` (string, required) — Must be a main file key (not a branch key).
- **Response:** `GetFileComponentsResponse` — Array of component metadata.
- **Errors:** 400, 403, 404, 429, 500

#### Get component

- **`GET /v1/components/{key}`**
- **Operation ID:** `getComponent`
- **Purpose:** Get metadata on a single component by its key.
- **Security:** `PersonalAccessToken` or `OAuth2` (`library_assets:read` or `files:read`)
- **Path parameters:**
  - `key` (string, required) — Component unique identifier.
- **Response:** `GetComponentResponse` — Component metadata including `key`, `file_key`, `node_id`, `thumbnail_url`, `name`, `description`, `created_at`, `updated_at`, `containing_frame`, `user`.
- **Errors:** 400, 403, 404, 429, 500

### 3h. Component Sets — 3 endpoints

**Implementation status:** Not Built — no provider functions, routes, or models exist for this resource. See gap analysis in `docs/FIGMA_IMPLEMENTATION_AUDIT.md`.

#### Get team component sets

- **`GET /v1/teams/{team_id}/component_sets`**
- **Operation ID:** `getTeamComponentSets`
- **Purpose:** Get paginated list of published component sets within a team library.
- **Security:** `PersonalAccessToken` or `OAuth2` (`team_library_content:read` or `files:read`)
- **Path/query parameters:** Same as `getTeamComponents`.
- **Response:** `GetTeamComponentSetsResponse` — Paginated component set metadata.
- **Errors:** 400, 403, 404, 429, 500

#### Get file component sets

- **`GET /v1/files/{file_key}/component_sets`**
- **Operation ID:** `getFileComponentSets`
- **Purpose:** Get published component sets within a file library.
- **Security:** `PersonalAccessToken` or `OAuth2` (`library_content:read` or `files:read`)
- **Path parameters:**
  - `file_key` (string, required) — Must be a main file key.
- **Response:** `GetFileComponentSetsResponse`
- **Errors:** 400, 403, 404, 429, 500

#### Get component set

- **`GET /v1/component_sets/{key}`**
- **Operation ID:** `getComponentSet`
- **Purpose:** Get metadata on a published component set by key.
- **Security:** `PersonalAccessToken` or `OAuth2` (`library_assets:read` or `files:read`)
- **Path parameters:**
  - `key` (string, required) — Component set unique identifier.
- **Response:** `GetComponentSetResponse`
- **Errors:** 400, 403, 404, 429, 500

### 3i. Styles — 3 endpoints

**Implementation status:** Not Built — no provider functions, routes, or models exist for this resource. See gap analysis in `docs/FIGMA_IMPLEMENTATION_AUDIT.md`.

#### Get team styles

- **`GET /v1/teams/{team_id}/styles`**
- **Operation ID:** `getTeamStyles`
- **Purpose:** Get paginated list of published styles within a team library.
- **Security:** `PersonalAccessToken` or `OAuth2` (`team_library_content:read` or `files:read`)
- **Path/query parameters:** Same as `getTeamComponents`.
- **Response:** `GetTeamStylesResponse` — Paginated style metadata with `key`, `file_key`, `node_id`, `style_type` (FILL, TEXT, EFFECT, GRID), `thumbnail_url`, `name`, `description`.
- **Errors:** 400, 403, 404, 429, 500

#### Get file styles

- **`GET /v1/files/{file_key}/styles`**
- **Operation ID:** `getFileStyles`
- **Purpose:** Get published styles within a file library.
- **Security:** `PersonalAccessToken` or `OAuth2` (`library_content:read` or `files:read`)
- **Path parameters:**
  - `file_key` (string, required) — Must be a main file key.
- **Response:** `GetFileStylesResponse`
- **Errors:** 400, 403, 404, 429, 500

#### Get style

- **`GET /v1/styles/{key}`**
- **Operation ID:** `getStyle`
- **Purpose:** Get metadata on a style by key.
- **Security:** `PersonalAccessToken` or `OAuth2` (`library_assets:read` or `files:read`)
- **Path parameters:**
  - `key` (string, required) — Style unique identifier.
- **Response:** `GetStyleResponse`
- **Errors:** 400, 403, 404, 429, 500

### 3j. Webhooks — 7 endpoints

**Implementation status:** Not Built — no provider functions, routes, or models exist for this resource. See gap analysis in `docs/FIGMA_IMPLEMENTATION_AUDIT.md`.

#### Get webhooks

- **`GET /v2/webhooks`**
- **Operation ID:** `getWebhooks`
- **Purpose:** List webhooks by context (team/project/file) or by plan (paginated).
- **Security:** `PersonalAccessToken` or `OAuth2` (`webhooks:read`)
- **Query parameters:**
  - `context` (string) — `"team"`, `"project"`, or `"file"`. Cannot use with `plan_api_id`.
  - `context_id` (string) — ID of the context. Cannot use with `plan_api_id`.
  - `plan_api_id` (string) — Plan ID to get all webhooks across contexts (paginated). Cannot use with `context`/`context_id`.
  - `cursor` (string) — Pagination cursor (only with `plan_api_id`).
- **Response:** `GetWebhooksResponse` — Array of webhook objects.
- **Errors:** 400, 403

#### Create webhook

- **`POST /v2/webhooks`**
- **Operation ID:** `postWebhook`
- **Purpose:** Create a new webhook. Sends a PING event to the endpoint on creation by default.
- **Security:** `PersonalAccessToken` or `OAuth2` (`webhooks:write`)
- **Request body:**
  - `event_type` (WebhookV2Event, required) — Event to subscribe to.
  - `context` (string, required) — `"team"`, `"project"`, or `"file"`.
  - `context_id` (string, required) — ID of the context to receive updates about.
  - `endpoint` (string, required) — HTTP endpoint URL (max 2048 chars).
  - `passcode` (string, required) — Verification string passed back to endpoint (max 100 chars).
  - `status` (WebhookV2Status) — `ACTIVE` (default) or `PAUSED`.
  - `description` (string) — Human-readable name/description (max 150 chars).
  - `team_id` (string, **deprecated**) — Use `context`/`context_id` instead.
- **Response:** `PostWebhookResponse` — Created webhook object with `id`, `event_type`, `context`, `context_id`, `status`, `endpoint`, `passcode`, `description`.
- **Errors:** 400, 403, 429, 500

#### Get webhook

- **`GET /v2/webhooks/{webhook_id}`**
- **Operation ID:** `getWebhook`
- **Purpose:** Get a webhook by ID.
- **Security:** `PersonalAccessToken` or `OAuth2` (`webhooks:read` or `files:read`)
- **Path parameters:**
  - `webhook_id` (string, required)
- **Response:** `GetWebhookResponse` — Webhook object (passcode returned as empty string for security).
- **Errors:** 400, 403, 404, 429, 500

#### Update webhook

- **`PUT /v2/webhooks/{webhook_id}`**
- **Operation ID:** `putWebhook`
- **Purpose:** Update a webhook's event type, endpoint, passcode, status, or description.
- **Security:** `PersonalAccessToken` or `OAuth2` (`webhooks:write`)
- **Path parameters:**
  - `webhook_id` (string, required)
- **Request body:**
  - `event_type` (WebhookV2Event, required)
  - `endpoint` (string, required)
  - `passcode` (string, required)
  - `status` (WebhookV2Status) — `ACTIVE` or `PAUSED`.
  - `description` (string)
- **Response:** `PutWebhookResponse`
- **Errors:** 400, 403, 404, 429, 500

#### Delete webhook

- **`DELETE /v2/webhooks/{webhook_id}`**
- **Operation ID:** `deleteWebhook`
- **Purpose:** Permanently delete a webhook. Cannot be reversed.
- **Security:** `PersonalAccessToken` or `OAuth2` (`webhooks:write`)
- **Path parameters:**
  - `webhook_id` (string, required)
- **Response:** `DeleteWebhookResponse`
- **Errors:** 400, 403, 404, 429, 500

#### Get team webhooks (Deprecated)

- **`GET /v2/teams/{team_id}/webhooks`**
- **Operation ID:** `getTeamWebhooks`
- **Purpose:** List all webhooks registered under a team. **Deprecated** — use `GET /v2/webhooks` with `context=team` instead.
- **Security:** `PersonalAccessToken` or `OAuth2` (`webhooks:read` or `files:read`)
- **Path parameters:**
  - `team_id` (string, required)
- **Response:** `GetTeamWebhooksResponse`
- **Errors:** 403, 404, 429, 500

#### Get webhook requests

- **`GET /v2/webhooks/{webhook_id}/requests`**
- **Operation ID:** `getWebhookRequests`
- **Purpose:** Returns all webhook delivery requests sent within the last week. Useful for debugging.
- **Security:** `PersonalAccessToken` or `OAuth2` (`webhooks:read` or `files:read`)
- **Path parameters:**
  - `webhook_id` (string, required)
- **Response:** `GetWebhookRequestsResponse` — Array of `WebhookV2Request` objects with `webhook_id`, `request_info`, `response_info`, `error_msg`.
- **Errors:** 400, 403, 404, 429, 500

### 3k. Activity Logs — 1 endpoint

**Implementation status:** Not Built — no provider functions, routes, or models exist for this resource. See gap analysis in `docs/FIGMA_IMPLEMENTATION_AUDIT.md`.

#### Get activity logs

- **`GET /v1/activity_logs`**
- **Operation ID:** `getActivityLogs`
- **Purpose:** Returns organization-level activity log events.
- **Security:** `OrgOAuth2` (`org:activity_log_read`) — requires organization admin OAuth
- **Query parameters:**
  - `events` (string) — Comma-separated event type(s) to include. All events returned by default.
  - `start_time` (number) — Unix timestamp of earliest event. Defaults to one year ago.
  - `end_time` (number) — Unix timestamp of latest event. Defaults to current time.
  - `limit` (number) — Max events to return. Defaults to 1000.
  - `order` (string, enum: `asc`, `desc`, default `asc`) — Order by timestamp.
- **Response:** `GetActivityLogsResponse` — Array of activity log event objects.
- **Errors:** 400, 401, 403, 429, 500

### 3l. Payments — 1 endpoint

**Implementation status:** Not Built — no provider functions, routes, or models exist for this resource. See gap analysis in `docs/FIGMA_IMPLEMENTATION_AUDIT.md`.

#### Get payments

- **`GET /v1/payments`**
- **Operation ID:** `getPayments`
- **Purpose:** Get payment info for a plugin, widget, or Community file. Only queryable for resources you own.
- **Security:** `PersonalAccessToken`
- **Query parameters (mutually exclusive identification):**
  - `plugin_payment_token` (string) — Short-lived token from `getPluginPaymentTokenAsync`.
  - `user_id` (string) — User ID (from OAuth). Use with one of the resource IDs below.
  - `community_file_id` (string) — Community file ID.
  - `plugin_id` (string) — Plugin ID.
  - `widget_id` (string) — Widget ID.
- **Response:** `GetPaymentsResponse` — Payment status and details.
- **Errors:** 401, 429, 500

### 3m. Variables — 3 endpoints

**Implementation status:** Not Built — no provider functions, routes, or models exist for this resource. See gap analysis in `docs/FIGMA_IMPLEMENTATION_AUDIT.md`.

#### Get local variables

- **`GET /v1/files/{file_key}/variables/local`**
- **Operation ID:** `getLocalVariables`
- **Purpose:** Enumerate local variables created in the file and remote variables used in the file. Returns full variable objects with values per mode.
- **Security:** `PersonalAccessToken` or `OAuth2` (`file_variables:read`)
- **Restriction:** Available to full members of Enterprise organizations only.
- **Path parameters:**
  - `file_key` (string, required) — File key or branch key.
- **Response:** `GetLocalVariablesResponse` — `variables` (map of variable ID → variable object), `variableCollections` (map of collection ID → collection object with modes). Remote variables are referenced by `subscribed_id`.
- **Errors:** 401, 403, 404, 429, 500

#### Get published variables

- **`GET /v1/files/{file_key}/variables/published`**
- **Operation ID:** `getPublishedVariables`
- **Purpose:** Returns variables published from the file (library variables). Includes `subscribed_id` for consumer reference. Modes are omitted.
- **Security:** `PersonalAccessToken` or `OAuth2` (`file_variables:read`)
- **Restriction:** Available to full members of Enterprise organizations only.
- **Path parameters:**
  - `file_key` (string, required) — Must be a main file key (not a branch key).
- **Response:** `GetPublishedVariablesResponse` — Variables and collections with `subscribed_id` and `updatedAt` timestamps. `subscribed_id` changes on each publish.
- **Errors:** 401, 403, 404, 429, 500

#### Create/modify/delete variables

- **`POST /v1/files/{file_key}/variables`**
- **Operation ID:** `postVariables`
- **Purpose:** Bulk create, update, and delete variables and variable collections. Atomic operation — all changes succeed or all fail.
- **Security:** `PersonalAccessToken` or `OAuth2` (`file_variables:write`)
- **Restriction:** Available to full members of Enterprise organizations with Editor seats.
- **Path parameters:**
  - `file_key` (string, required) — File key or branch key.
- **Request body (at least one array required):**
  - `variableCollections` (array of `VariableCollectionChange`) — Create, update, or delete collections.
  - `variableModes` (array of `VariableModeChange`) — Create, update, or delete modes. Max 40 modes per collection. Mode names max 40 chars.
  - `variables` (array of `VariableChange`) — Create, update, or delete variables. Max 5000 per collection. Names must be unique within a collection.
  - `variableModeValues` (array of `VariableModeValue`) — Set variable values for specific modes. Alias cycles are forbidden.
- **Constraints:**
  - Request body max 4MB.
  - Each object must include an `action` property (`CREATE`, `UPDATE`, or `DELETE`).
  - Temporary IDs can be used to reference objects created within the same request (e.g., create collection with temp ID, reference it in new variables).
  - `tempIdToRealId` mapping returned in response.
  - Remote variables cannot be updated — only edit in the originating file.
- **Response:** `PostVariablesResponse` — `tempIdToRealId` mapping.
- **Errors:** 400, 401, 403, 404, 429, 500

### 3n. Dev Resources — 4 endpoints

**Implementation status:** Not Built — no provider functions, routes, or models exist for this resource. See gap analysis in `docs/FIGMA_IMPLEMENTATION_AUDIT.md`.

#### Get dev resources

- **`GET /v1/files/{file_key}/dev_resources`**
- **Operation ID:** `getDevResources`
- **Purpose:** Get dev resources in a file (links between design nodes and code/external URLs).
- **Security:** `PersonalAccessToken` or `OAuth2` (`file_dev_resources:read`)
- **Path parameters:**
  - `file_key` (string, required) — Must be a main file key.
- **Query parameters:**
  - `node_ids` (string) — Comma-separated node IDs to filter by. Omit for all dev resources.
- **Response:** `GetDevResourcesResponse` — Array of dev resource objects.
- **Errors:** 400, 401, 403, 404, 429, 500

#### Create dev resources

- **`POST /v1/dev_resources`**
- **Operation ID:** `postDevResources`
- **Purpose:** Bulk create dev resources across multiple files. Max 10 dev resources per node. Duplicate URLs per node are rejected.
- **Security:** `PersonalAccessToken` or `OAuth2` (`file_dev_resources:write`)
- **Request body:**
  - `dev_resources` (array, required) — Each item: `name` (string, required), `url` (string, required), `file_key` (string, required), `node_id` (string, required).
- **Response:** `PostDevResourcesResponse` — `links_created` (successful) and `errors` (failed) arrays.
- **Errors:** 400, 401, 403, 429, 500

#### Update dev resources

- **`PUT /v1/dev_resources`**
- **Operation ID:** `putDevResources`
- **Purpose:** Bulk update dev resources across multiple files.
- **Security:** `PersonalAccessToken` or `OAuth2` (`file_dev_resources:write`)
- **Request body:**
  - `dev_resources` (array, required) — Each item: `id` (string, required), `name` (string), `url` (string).
- **Response:** `PutDevResourcesResponse` — `links_updated` and `errors` arrays.
- **Errors:** 400, 401, 403, 429, 500

#### Delete dev resource

- **`DELETE /v1/files/{file_key}/dev_resources/{dev_resource_id}`**
- **Operation ID:** `deleteDevResource`
- **Purpose:** Delete a dev resource from a file.
- **Security:** `PersonalAccessToken` or `OAuth2` (`file_dev_resources:write`)
- **Path parameters:**
  - `file_key` (string, required) — Must be a main file key.
  - `dev_resource_id` (string, required)
- **Response:** `DeleteDevResourceResponse`
- **Errors:** 401, 403, 404, 429, 500

### 3o. Library Analytics — 6 endpoints

**Implementation status:** Not Built — no provider functions, routes, or models exist for this resource. See gap analysis in `docs/FIGMA_IMPLEMENTATION_AUDIT.md`.

All six endpoints follow the same pattern. Each returns analytics data for a published library file, grouped by a specified dimension.

**Common parameters (all endpoints):**
- **Path:** `file_key` (string, required) — Library file key.
- **Query:** `cursor` (string) — Pagination cursor. `group_by` (string, required) — Grouping dimension (varies by endpoint). `start_date` (string, ISO 8601 YYYY-MM-DD) — Earliest week. `end_date` (string, ISO 8601 YYYY-MM-DD) — Latest week.
- **Security:** `PersonalAccessToken` or `OAuth2` (`library_analytics:read`)
- **Errors:** 400, 401, 403, 429, 500

| Endpoint | Operation ID | Group By Options |
|----------|-------------|-----------------|
| `GET /v1/analytics/libraries/{file_key}/component/actions` | `getLibraryAnalyticsComponentActions` | `component`, `team` |
| `GET /v1/analytics/libraries/{file_key}/component/usages` | `getLibraryAnalyticsComponentUsages` | `component`, `file` |
| `GET /v1/analytics/libraries/{file_key}/style/actions` | `getLibraryAnalyticsStyleActions` | `style`, `team` |
| `GET /v1/analytics/libraries/{file_key}/style/usages` | `getLibraryAnalyticsStyleUsages` | `style`, `file` |
| `GET /v1/analytics/libraries/{file_key}/variable/actions` | `getLibraryAnalyticsVariableActions` | `variable`, `team` |
| `GET /v1/analytics/libraries/{file_key}/variable/usages` | `getLibraryAnalyticsVariableUsages` | `variable`, `file` |

---

## Section 4: Figma Embed API

### 4a. Overview

The Figma Embed API enables embedding live Figma designs and prototypes in web applications via iframe. It provides bidirectional communication: the host page can send messages to control embedded prototypes, and the embedded prototype can send events back to the host page.

Embed Kit 2.0 is the current version. Migration from Embed Kit 1.0 involves converting URL format (subdomain change from `www` to `embed`, parameter names from underscores to hyphens, removal of `embed_origin` parameter).

### 4b. Setup Requirements

1. **Create an OAuth application** at Figma's developer portal with name, website, and logo
2. **Obtain a client ID** from the OAuth app configuration
3. **Register embed origins** via Embed API settings to whitelist domains where embeds will appear
4. **Add the `client-id` parameter** to the iframe src URL

### 4c. Embed URL Format and Conversion

**Base format:**
```
https://embed.figma.com/proto/{FILE_ID}/{FILE_NAME}
  ?node-id={NODE_ID}
  &embed-host={DOMAIN}
  &client-id={CLIENT_ID}
```

**URL conversion:** Replace `www.figma.com` or `figma.com` with `embed.figma.com`, then add query parameters.

**Supported file types:**

| File Type | URL Pattern |
|-----------|-------------|
| FigJam boards | `https://www.figma.com/board/:file_key/:file_name` |
| Figma Slides | `https://www.figma.com/slides/:file_key/:file_name` |
| Slides presentation | `https://www.figma.com/deck/:file_key/:file_name` |
| Design files | `https://www.figma.com/design/:file_key/:file_name` |
| Dev Mode | `https://www.figma.com/design/:file_key/:file_name?m=dev` |

**Query parameters:**

| Parameter | Required | Description |
|-----------|----------|-------------|
| `embed-host` | Yes | Your domain name |
| `client-id` | For Embed API | OAuth app client ID |
| `node-id` | No | Specific node to display |
| `m` | No | Mode (`dev` for Dev Mode) |

**URL validation regex:**
```javascript
const URL_REGEX = /https:\/\/[\w\.-]+\.?figma.com\/([\w-]+)\/([0-9a-zA-Z]{22,128})(?:\/.*)?$/
```

### 4d. Message Types (Controlling Prototypes)

Send messages to the embedded prototype via `postMessage`. Target origin must always be `https://www.figma.com`.

| Type | Purpose | Data Payload |
|------|---------|-------------|
| `NAVIGATE_TO_FRAME_AND_CLOSE_OVERLAYS` | Navigate to a specific frame and close any open overlays | `{ nodeId: string }` |
| `NAVIGATE_FORWARD` | Move to the next frame in the prototype flow | (none) |
| `NAVIGATE_BACKWARD` | Move to the previous frame | (none) |
| `CHANGE_COMPONENT_STATE` | Change a component instance to a different variant | `{ nodeId: string, newVariantId: string }` |
| `RESTART` | Reset prototype to the starting node | (none) |

**Example:**
```javascript
iframe.contentWindow.postMessage(
  { type: "NAVIGATE_TO_FRAME_AND_CLOSE_OVERLAYS", nodeId: "123:456" },
  "https://www.figma.com"
);
```

### 4e. Event Types (From Prototype)

Listen for events from the embedded prototype via `window.addEventListener("message", ...)`. Always verify `event.origin === "https://www.figma.com"`.

| Event | Description | Data Payload |
|-------|-------------|-------------|
| `MOUSE_PRESS_OR_RELEASE` | Click tracking with position data | `{ x, y }` |
| `PRESENTED_NODE_CHANGED` | Frame or overlay navigation occurred | `{ nodeId }` |
| `INITIAL_LOAD` | Prototype finished loading | (none) |
| `NEW_STATE` | Component instance state changed | (state data) |
| `REQUEST_CLOSE` | User pressed spacebar (close request) | (none) |
| `LOGIN_SCREEN_SHOWN` | Authentication required — user needs to log in | (none) |
| `PASSWORD_SCREEN_SHOWN` | Password entry needed for protected file | (none) |

**Node ID discovery from events:** `MOUSE_PRESS_OR_RELEASE`, `PRESENTED_NODE_CHANGED`, and `NEW_STATE` events include node IDs that can be used with the Embed API and REST API.

### 4f. Access Control and Customization

**Audience levels:**
- **Organization-only** — Only org members can view
- **Public** — Anyone with the link can view

**Permission levels:**
- **Can view** — Read-only access
- **Can edit** — Full editing access

**Restrictions:**
- Password-protected files cannot be embedded
- Organization files require user authentication

**Customization options:**
- Control pan and zoom functionality
- Page selection capabilities
- Design or Dev Mode specification (`m=dev`)
- Full-screen expansion permissions
- Theme application (dark, light, or system)

### 4g. Limitations

- Embeds only work in **browser-based applications**
- Cannot embed in native/desktop applications
- Password-protected content cannot be embedded
- Organization-restricted files require the viewer to be authenticated in Figma

---

## Section 5: Export Capabilities

The image export endpoint (`GET /v1/images/{file_key}`) is the most OEX-relevant capability, enabling programmatic export of design assets for the direct mail creative pipeline.

### Image Export Endpoint

**`GET /v1/images/{file_key}`** (`getImages`)

**Supported formats:**

| Format | Use Case | Notes |
|--------|----------|-------|
| `png` (default) | Raster images, postcard/letter graphics | Best for photographic content |
| `jpg` | Compressed raster images | Smaller file size, lossy compression |
| `svg` | Vector graphics, scalable assets | Supports `svg_include_id`, `svg_include_node_id`, `svg_simplify_stroke`, `svg_outline_text` options |
| `pdf` | Print-ready documents | Ideal for Lob direct mail templates |

**Export settings:**

| Setting | Range | Default | Description |
|---------|-------|---------|-------------|
| `scale` | 0.01–4 | 1 | Image scaling factor (4x = 300 DPI at standard screen resolution) |
| `format` | jpg/png/svg/pdf | png | Output format |
| `svg_outline_text` | boolean | true | Render text as vector paths (guarantees visual accuracy) |
| `svg_include_id` | boolean | false | Add layer names as `id` attributes |
| `svg_include_node_id` | boolean | false | Add node IDs as `data-node-id` attributes |
| `svg_simplify_stroke` | boolean | true | Use stroke attributes instead of masks |
| `contents_only` | boolean | true | Exclude overlapping content |
| `use_absolute_bounds` | boolean | false | Export full dimensions (useful for text) |

**Batch export:** Pass multiple comma-separated `ids` to export multiple nodes in one call:
```
GET /v1/images/{file_key}?ids=1:2,1:3,1:4&format=pdf&scale=4
```

**Response:** `images` object mapping node IDs to temporary download URLs. URLs expire after **30 days**. Images exceeding 32 megapixels are scaled down. Nodes that fail to render return `null`.

### Lob Pipeline Integration

Exported assets from Figma can directly feed into the Lob direct mail workflow:

1. **Postcard creative:** Export front/back designs as PNG or PDF at 4x scale (300 DPI) → pass URLs to Lob's `create_postcard()` as `front`/`back` parameters.
2. **Letter creative:** Export letter template as PDF → pass URL to Lob's `create_letter()` as `file` parameter.
3. **HTML templates:** Export SVG for inline embedding in Lob HTML templates with merge variables for per-lead personalization.
4. **Batch variation:** Export multiple frame variations (A/B test designs) in a single API call using comma-separated `ids`.

---

## Section 6: Webhooks Deep Dive

### Webhook v2 API

All webhook management endpoints use the `/v2/` prefix. Webhooks can be scoped to teams, projects, or files via the `context` and `context_id` parameters.

### Event Types

The `WebhookV2Event` enum defines subscribable events:

| Event Type | Description | Trigger |
|-----------|-------------|---------|
| `PING` | Webhook creation verification | Auto-sent on webhook creation. Cannot be subscribed to — all webhooks receive PING events. |
| `FILE_UPDATE` | File content changed | Triggers within 30 minutes of editing inactivity. Useful for staying up-to-date with file contents (e.g., regenerate static sites from Figma). |
| `FILE_VERSION_UPDATE` | Named version created | Triggers when a named version is created in version history. Useful for asset deployment workflows. |
| `FILE_DELETE` | File deleted | Triggers when a file is deleted. Subscribing to `FILE_UPDATE` automatically includes these. Does NOT trigger for files inside a deleted folder. |
| `LIBRARY_PUBLISH` | Library file published | Triggers when a library file is published. Separate events fire for each asset type changed (components, styles, variables). Useful for design system sync. |
| `FILE_COMMENT` | Comment posted on file | Triggers when someone comments. Useful for Slack/Jira integrations. |
| `DEV_MODE_STATUS_UPDATE` | Dev Mode layer status changed | Triggers when a layer's Dev Mode status changes. Useful for task management integrations. |

### Webhook Payload Shapes

Each event type has a corresponding payload schema:

| Event | Payload Schema | Key Fields |
|-------|---------------|------------|
| `PING` | `WebhookPingPayload` | `webhook_id`, `timestamp` |
| `FILE_UPDATE` | `WebhookFileUpdatePayload` | `file_key`, `file_name`, `timestamp` |
| `FILE_VERSION_UPDATE` | `WebhookFileVersionUpdatePayload` | `file_key`, `file_name`, `version_id`, `label`, `description`, `timestamp` |
| `FILE_DELETE` | `WebhookFileDeletePayload` | `file_key`, `file_name`, `timestamp` |
| `LIBRARY_PUBLISH` | `WebhookLibraryPublishPayload` | `file_key`, `file_name`, `created_components`, `modified_components`, `deleted_components`, `created_styles`, `modified_styles`, `deleted_styles`, `timestamp` |
| `FILE_COMMENT` | `WebhookFileCommentPayload` | `file_key`, `file_name`, `comment`, `timestamp` |
| `DEV_MODE_STATUS_UPDATE` | `WebhookDevModeStatusUpdatePayload` | `file_key`, `file_name`, `node_id`, `new_status`, `timestamp` |

### Passcode Verification

- The `passcode` field (max 100 chars) is set when creating a webhook and included in every webhook delivery
- Use the passcode to verify that requests originate from Figma
- When reading webhooks via GET endpoints, the passcode is returned as an empty string for security

### Delivery and Retry Behavior

- Figma expects a **200** response from your endpoint
- Non-200 responses or timeouts are treated as errors
- Figma retries failed requests **3 times** with exponential backoff
- Webhook delivery log is available via `GET /v2/webhooks/{webhook_id}/requests` (last 7 days)

### Webhook Status

| Status | Description |
|--------|-------------|
| `ACTIVE` | Webhook is healthy and receives all events |
| `PAUSED` | Webhook is paused and will not receive any events |

### Context Scoping

Webhooks can be scoped to different contexts:

| Context | Scope | Use Case |
|---------|-------|----------|
| `team` | All files in a team | Broad monitoring (all design changes) |
| `project` | All files in a project | Project-level monitoring |
| `file` | Single file | Targeted monitoring (specific template file) |

---

## Section 7: Variables and Design Tokens

### What Figma Variables Are

Variables are reusable values in Figma that can be applied to design properties such as colors, typography, spacing, and sizing. They form the foundation of design token systems and support multi-mode configurations (e.g., light/dark theme, responsive breakpoints).

### Variable Types

From the OpenAPI spec and TypeScript type definitions:

| Type | Description | Example Values |
|------|-------------|---------------|
| `BOOLEAN` | True/false values | `true`, `false` |
| `FLOAT` | Numeric values (spacing, sizing, opacity) | `16`, `1.5`, `0.8` |
| `STRING` | Text values (font families, labels) | `"Inter"`, `"primary"` |
| `COLOR` | Color values (RGBA) | `{ r: 0.2, g: 0.4, b: 0.8, a: 1.0 }` |

### Variable Collections and Modes

- **Collections** group related variables (e.g., "Colors", "Spacing", "Typography")
- **Modes** provide different value sets within a collection (e.g., "Light" and "Dark" modes for a Colors collection)
- Max 40 modes per collection
- Max 5000 variables per collection
- Mode names max 40 characters
- Variable names must be unique within a collection

### Reading Variables

**`GET /v1/files/{file_key}/variables/local`** — Returns full variable tree with values per mode:
- `variables` — Map of variable ID → variable object (name, type, values per mode, scope, code syntax)
- `variableCollections` — Map of collection ID → collection object with modes
- Includes both local variables and remote (subscribed) variables used in the file

**`GET /v1/files/{file_key}/variables/published`** — Library variables for consumption:
- Includes `subscribed_id` for consumer reference (changes on each publish)
- Modes are omitted — use `GET /local` in the source file to examine mode values
- `updatedAt` timestamps indicate last publish time

### Writing Variables

**`POST /v1/files/{file_key}/variables`** — Atomic bulk operations:
- **Create:** Set `action: "CREATE"` with variable definition. Use temporary IDs for cross-referencing within the same request.
- **Update:** Set `action: "UPDATE"` with variable ID and changed fields.
- **Delete:** Set `action: "DELETE"` with variable ID.
- **Set mode values:** Use the `variableModeValues` array with `variableId`, `modeId`, and `value`.
- Aliases (variable references) are supported but cycles are forbidden.

### Enterprise-Only Restriction

Variables endpoints require membership in a Figma Enterprise organization. The OAuth scopes `file_variables:read` and `file_variables:write` are only available to Enterprise org members. Non-Enterprise requests will receive a 403 error.

---

## Section 8: Rate Limits

The Figma OpenAPI specification does not document specific per-endpoint rate limits or rate limit headers. Rate limiting behavior is managed server-side.

**Known information from the specification:**
- HTTP 429 (Too Many Requests) responses are defined for all endpoints
- The spec does not specify request-per-second limits, burst limits, or rate limit headers

**Refer to Figma's developer documentation for current rate limit details:**
- https://www.figma.com/developers/api (general rate limit guidance)
- Rate limits may vary by plan tier and endpoint category

**Recommended approach for OEX integration:**
- Implement exponential backoff on 429 responses
- Cache file data aggressively (file content changes infrequently)
- Use webhooks for change notification instead of polling
- Batch image exports using the `ids` parameter to reduce request count

---

## Section 9: Error Handling

### Error Response Format

The OpenAPI spec defines two error response patterns:

**Pattern 1: Error with message**
```json
{
  "status": 400,
  "err": "Error description message"
}
```
Used by: Files, Comments, Components, Component Sets, Styles, Webhooks (some endpoints)

**Pattern 2: Error with boolean**
```json
{
  "status": 400,
  "error": true
}
```
Used by: Projects, Comment Reactions, Webhooks (some endpoints), Activity Logs, Payments, Variables, Dev Resources, Library Analytics

### Common HTTP Status Codes

| Status | Meaning | Common Causes |
|--------|---------|--------------|
| 400 | Bad Request | Invalid parameters, malformed request body, missing required fields |
| 401 | Unauthorized | Invalid or expired token, missing authentication |
| 403 | Forbidden | Insufficient permissions, file not accessible, Enterprise-only endpoint accessed by non-Enterprise user |
| 404 | Not Found | File, node, comment, or webhook does not exist |
| 429 | Too Many Requests | Rate limit exceeded — implement backoff and retry |
| 500 | Internal Server Error | Server-side error — retry with backoff |

### Error Handling Recommendations

- Check for both `err` (string) and `error` (boolean) fields in error responses
- Implement retry logic with exponential backoff for 429 and 500 errors
- For 403 errors on Variables endpoints, verify Enterprise plan membership
- For `null` values in image export responses, the specific node failed to render — log and skip rather than retrying

---

## Section 10: Use Case Mapping to OEX Workflows

### Direct Mail Creative Pipeline

**Workflow:** Design postcard/letter templates in Figma → export via API → feed into Lob for printing.

- Design postcard front/back in Figma as separate frames
- Use `GET /v1/images/{file_key}?ids={front_node},{back_node}&format=pdf&scale=4` to export at 300 DPI
- Pass exported PDF URLs to Lob `create_postcard()` as `front`/`back` parameters
- For personalized content: read text layer values via `GET /v1/files/{file_key}/nodes`, map placeholder text to Lob merge variables
- Use Figma variables for brand colors/typography → ensure consistency across all creative

### Landing Page Design

**Workflow:** Design pages in Figma for fleets.live, ColdEmail.com, etc. → export assets → use in Next.js frontends.

- Export hero images, icons, and illustrations via `GET /v1/images/{file_key}` as SVG or PNG
- Use the Variables API to sync brand colors and typography tokens to frontend component systems
- Track design iterations with `GET /v1/files/{file_key}/versions`

### Campaign Creative Templates

**Workflow:** Create branded outbound assets in Figma → export programmatically for campaign variations.

- Design template frames with variant component instances (different CTAs, layouts, color schemes)
- Export all variations in a single batch call: `GET /v1/images/{file_key}?ids={variant1},{variant2},{variant3}`
- Use file versioning (`GET /v1/files/{file_key}/versions`) to track creative iterations across campaign cycles
- Use components API to list available template components for creative selection UI

### Live Embeds for Demos

**Workflow:** Embed Figma designs in OEX dashboard or demo pages to show direct mail creative previews.

- Embed design files via `https://embed.figma.com/design/{file_key}/{file_name}?embed-host={domain}&client-id={client_id}`
- Use Embed API message passing to navigate between postcard front/back views
- Listen for `PRESENTED_NODE_CHANGED` events to track which creative frame is being viewed
- Show real-time design previews before committing to Lob print production

### Design Token Sync

**Workflow:** Read Figma variables → sync brand tokens to frontend component systems.

- Read variables via `GET /v1/files/{file_key}/variables/local` to get colors, typography, spacing values per mode
- Map Figma modes (Light/Dark) to frontend theme configurations
- Subscribe to `LIBRARY_PUBLISH` webhook events to trigger automatic token re-sync when designers update the design system
- Generate CSS custom properties or theme configuration files from variable data

### Automated Asset Generation

**Workflow:** Programmatically read templates, swap content via variables, export personalized creative per campaign batch.

- Read template file structure via `GET /v1/files/{file_key}/nodes` to identify text layers and image fills
- Use `POST /v1/files/{file_key}/variables` to set per-lead variable values (company name, personalized messaging)
- Export personalized frames via `GET /v1/images/{file_key}` per lead batch
- Feed exported assets into Lob's mail piece creation for mass personalized direct mail

### Webhook-Driven Workflows

**Workflow:** Subscribe to design change events → trigger automated re-export and refresh.

- Create webhook: `POST /v2/webhooks` with `event_type: "FILE_UPDATE"`, scoped to the template file
- On `FILE_UPDATE` event: re-export creative assets via `GET /v1/images/{file_key}`
- Refresh Lob template assets automatically when a designer updates a postcard or letter template
- Subscribe to `LIBRARY_PUBLISH` for design system changes that affect all templates
- Use `FILE_VERSION_UPDATE` to trigger exports only when designers explicitly tag a version as ready

---

## Section 11: Figma MCP vs REST API Comparison

### 11a. MCP Tools with REST API Equivalents

| MCP Tool | Likely REST API Call(s) | Notes |
|----------|------------------------|-------|
| `get_design_context` | `GET /v1/files/{file_key}/nodes` + `GET /v1/images/{file_key}` | MCP enriches with generated code, Code Connect snippets, design annotations, and design tokens as CSS variables |
| `get_screenshot` | `GET /v1/images/{file_key}` | MCP adds desktop app integration and automatic format/scale selection |
| `get_metadata` | `GET /v1/files/{file_key}/nodes` | MCP returns simplified XML (IDs, types, names, positions, sizes) instead of full JSON |
| `get_variable_defs` | `GET /v1/files/{file_key}/variables/local` | MCP returns resolved variable values (e.g., `{'icon/default/secondary': '#949494'}`) instead of raw variable objects |
| `whoami` | `GET /v1/me` | Direct equivalent — returns authenticated user info |

### 11b. MCP-Exclusive Capabilities (No REST API Equivalent)

| MCP Tool | Capability | Why No REST Equivalent |
|----------|-----------|----------------------|
| `generate_figma_design` | Capture/import web pages into Figma | Write-back capability requiring Figma desktop app or platform integration |
| `generate_diagram` | Create FigJam diagrams from Mermaid syntax | Write-back capability for diagram creation |
| `create_design_system_rules` | AI-generated design system rules for a repo | AI/ML capability not available via REST |
| `get_code_connect_suggestions` | AI-suggested Code Connect mapping strategy | AI/ML capability for code-to-design linking |
| `add_code_connect_map` | Create Code Connect mapping (node → code component) | Code Connect is a platform feature managed through specialized APIs, not the public REST API |
| `send_code_connect_mappings` | Bulk save Code Connect mappings | Bulk Code Connect write, same as above |
| `get_code_connect_map` | Read Code Connect mappings for a node | Code Connect read, same as above |
| `get_figjam` | Generate UI code from FigJam nodes | MCP-specific code generation for FigJam content |

### 11c. REST API Capabilities Not Exposed via MCP

| REST API Capability | Endpoints | Relevance to OEX |
|--------------------|-----------|-------------------|
| Comments CRUD | 3 endpoints (get, post, delete) | Low — design review workflow |
| Comment Reactions | 3 endpoints (get, post, delete) | Low — design review |
| Projects browsing | 2 endpoints (team projects, project files) | Medium — file discovery |
| Version history | 1 endpoint (file versions) | Medium — creative iteration tracking |
| Webhooks management | 7 endpoints (full CRUD + delivery log) | **High** — change-driven automation |
| Activity logs | 1 endpoint (org admin) | Low — audit trail |
| Payments | 1 endpoint (plugin/widget) | None — not relevant to OEX |
| Library analytics | 6 endpoints (component/style/variable usage) | Low — design system metrics |
| Dev resources CRUD | 4 endpoints (link designs to code) | Medium — design-code linking |
| File metadata | 1 endpoint (lightweight file info) | Medium — file discovery |
| Image fills | 1 endpoint (user-uploaded images) | Medium — asset extraction |
| Team components/styles/component sets | 9 endpoints (team-level browsing) | Medium — template discovery |

### 11d. When to Use MCP vs REST API

| Use Case | Recommended | Reason |
|----------|-------------|--------|
| Design-to-code workflows | **MCP** | `get_design_context` provides enriched code output with framework adaptation |
| Interactive development in Cursor IDE | **MCP** | Direct integration with IDE context (languages, frameworks) |
| Server-side OEX provider adapter | **REST API** | Needs to run in automated pipelines without IDE |
| Webhook-driven automation | **REST API** | Webhook CRUD not available via MCP |
| CI/CD asset export pipelines | **REST API** | Automated, non-interactive execution |
| Bulk image export | **REST API** | `GET /v1/images/{file_key}` with batch `ids` parameter |
| Design token synchronization | **REST API** | Variables API for programmatic read/write |
| Template file monitoring | **REST API** | Webhooks for change detection |
| Diagram creation in FigJam | **MCP** | `generate_diagram` has no REST equivalent |
| Web page capture to Figma | **MCP** | `generate_figma_design` has no REST equivalent |

---

## Section 12: Credential Configuration

### Personal Access Token

| Variable | Value | Purpose |
|----------|-------|---------|
| `FIGMA_ACCESS_TOKEN` (recommended) | Token from Figma account settings | Server-side OEX provider adapter authentication |

- Obtained from: Figma → Settings → Personal Access Tokens → Generate New Token
- Suitable for: Server-side integrations, automated pipelines, CI/CD
- Scope: Full access to all endpoints the token owner has permission for

### OAuth 2.0

| Variable | Value | Purpose |
|----------|-------|---------|
| `FIGMA_OAUTH_CLIENT_ID` (recommended) | OAuth app client ID | User-delegated access + Embed API |
| `FIGMA_OAUTH_CLIENT_SECRET` (recommended) | OAuth app client secret | Token exchange |

- **Authorization URL:** `https://www.figma.com/oauth`
- **Token URL:** `https://api.figma.com/v1/oauth/token`
- **Refresh URL:** `https://api.figma.com/v1/oauth/refresh`
- **Flow:** Authorization Code (server-side) or PKCE (client-side)
- Suitable for: User-facing applications with delegated access, Embed API

### Embed API

- Requires the same OAuth app client ID (`FIGMA_OAUTH_CLIENT_ID`)
- Embed origins must be registered in the Figma developer portal (whitelist of domains where embeds are allowed)
- No separate secret needed for embedding — client ID is passed as a query parameter in the iframe URL

### Test vs Production

Figma does not have a test/sandbox mode like Lob. All API calls operate on real files and real data. There is no test API key prefix convention.

**Recommended testing strategy:**
- Create a dedicated test team/project in Figma for development
- Use test files with placeholder designs for integration testing
- Use file versioning to revert test changes
- OAuth token scoping can limit access to specific capabilities

---

## Section 13: Current Implementation Status

Reference: `docs/FIGMA_IMPLEMENTATION_AUDIT.md`

| Resource | Endpoints | Status |
|----------|-----------|--------|
| Files | 5 | Not Built |
| Comments | 3 | Not Built |
| Comment Reactions | 3 | Not Built |
| Users | 1 | Not Built |
| Projects | 2 | Not Built |
| Version History | 1 | Not Built |
| Components | 3 | Not Built |
| Component Sets | 3 | Not Built |
| Styles | 3 | Not Built |
| Webhooks | 7 | Not Built |
| Activity Logs | 1 | Not Built |
| Payments | 1 | Not Built |
| Variables | 3 | Not Built |
| Dev Resources | 4 | Not Built |
| Library Analytics | 6 | Not Built |
| **Total** | **46** | **0 Built** |

No Figma provider directory, router endpoints, Pydantic models, service functions, configuration variables, or orchestrator mappings exist in the OEX codebase. The Figma MCP server (13 tools) is available in the development environment for interactive design-to-code workflows but does not constitute a server-side integration.

For future integration planning, the highest-priority endpoints for OEX are:
1. **`GET /v1/images/{file_key}`** (getImages) — Export designs as PNG/PDF for Lob templates
2. **`GET /v1/files/{file_key}/nodes`** (getFileNodes) — Read design structure for template mapping
3. **`POST /v2/webhooks`** + webhook management — Change-driven creative refresh
4. **`GET /v1/files/{file_key}/variables/local`** (getLocalVariables) — Design token synchronization
5. **`GET /v1/me`** (getMe) — API key validation
