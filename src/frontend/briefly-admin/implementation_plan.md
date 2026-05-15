# Briefly Admin React App Implementation Plan

## Goal
Build a lightweight admin web app that:
- Lists articles with server-side pagination.
- Lists feeds with pagination UI.
- Looks simple overall, but presents articles in a news-like layout.
- Defers feed/article management actions until supporting backend endpoints exist.

## Scope and Constraints
- Frontend app location: `src/frontend/briefly-admin`.
- Backend API currently available from `public-api` for feed and article reads.
- Management actions are intentionally staged for later.
- Preferred styling approach: Tailwind CSS.

## Current Backend Capabilities (Confirmed)

### Available now
- `GET /feed` with `limit` and `offset` pagination.
- `GET /feed/search` with query + pagination.
- `GET /feed/articles/{article_id}` for article detail.

### Related but not full admin management
- `POST /sources` (create source).
- `POST /me/subscriptions` (create subscription).
- `DELETE /me/subscriptions/{source_id}` (delete subscription).

### Missing for full admin management
- Dedicated feed/source listing endpoint designed for admin usage.
- Dedicated source/feed update endpoint.
- Dedicated source/feed delete endpoint.
- Bulk actions (archive, reprocess, disable source, etc.).

## Product Direction

### UX tone
- Admin app should remain simple and clear.
- Articles section should feel like a small editorial/news experience.
- Feeds section should feel operational and utilitarian.

### Information architecture
- `/articles`: main news-like list view + search + pagination.
- `/articles/:id`: article detail/metadata view.
- `/feeds`: feed list page (read-only placeholder first), with paging controls and future management action slots.

## Phased Delivery Plan

## Phase 0: Foundation
Objective: get a stable shell and maintainable frontend structure.

Tasks:
- Bootstrap React + TypeScript app in `src/frontend/briefly-admin` (Vite).
- Install and configure Tailwind CSS as the default styling system.
- Add routing (React Router).
- Add data fetching and caching layer (TanStack Query).
- Add API client abstraction (Axios or fetch wrapper).
- Add environment config (`VITE_API_BASE_URL`).
- Add baseline linting/formatting and basic scripts.

Deliverable:
- Running app with skeleton routes and shared layout.

## Phase 1: Articles List (News-like)
Objective: implement high-value read path with stronger visual treatment.

Tasks:
- Integrate `GET /feed` with `limit/offset`.
- Add pagination controls:
  - `page`
  - `pageSize`
  - computed `offset = (page - 1) * pageSize`
  - total pages from response `total`
- Add search bar wired to `GET /feed/search`.
- Build news-like UI sections:
  - Featured lead story card.
  - Grid of secondary stories.
  - Compact headline rail/sidebar.
- Show article metadata where available:
  - title, source_id, published_at, language, categories.
  - image-based card style when `image_ref` exists.

Deliverable:
- Fully usable `/articles` page with paging and search.

## Phase 2: Article Detail
Objective: provide inspectable article details for admin workflows.

Tasks:
- Integrate `GET /feed/articles/{article_id}`.
- Build detail page with:
  - title and canonical URL.
  - category/topic chips.
  - language and sentiment.
  - technical metadata panel (`content_ref`, `image_ref`, `cluster_id`, `model_version`).
- Handle missing content gracefully (metadata-first rendering).

Deliverable:
- `/articles/:id` page with complete available read-model data.

## Phase 3: Feeds Page (Read-first)
Objective: stand up the section now, prepare for future management.

Tasks:
- Implement `/feeds` route and page shell.
- Add table/list layout with pagination controls.
- If no listing endpoint exists yet:
  - show explicit "data source not available yet" state.
  - include mock row structure behind dev-only fallback.
- Add reserved action slots (disabled buttons) for:
  - Create feed/source.
  - Edit feed/source.
  - Delete feed/source.
  - Subscribe/unsubscribe operations.

Deliverable:
- `/feeds` page with stable UX contract, ready for backend completion.

## Phase 4: Management Features (Future)
Objective: enable full admin operations once endpoints are ready.

Planned backend requirements:
- List feeds/sources endpoint for admin.
- Update source endpoint.
- Delete source endpoint.
- Optional moderation lifecycle endpoints (disable/retry/reindex).

Frontend tasks when ready:
- Activate action buttons and forms.
- Add optimistic or pessimistic mutation patterns.
- Add confirmation dialogs and error handling.
- Add activity toasts and audit-friendly UI hints.

Deliverable:
- Complete feed management workflow in admin UI.

## UI Guidelines

### Global
- Keep spacing and interactions simple.
- Prioritize readable typography and dense-but-clear metadata.
- Avoid visual noise in non-article areas.
- Use Tailwind utility classes for layout, spacing, typography, and responsive behavior.

### Articles page visual style
- More editorial hierarchy than dashboard cards.
- Strong headline scale and date/source metadata.
- Distinct featured card treatment.
- Mobile-friendly stacking order:
  - featured first
  - story grid second
  - headline rail last

### Feeds page visual style
- More operational, table-oriented layout.
- Keep interactions obvious and low-friction.
- Reserve areas for future controls without confusing users.

## Technical Design Notes
- Use route-level query params for list state:
  - `?page=2&pageSize=20&q=ai`
- Keep pagination server-driven and deterministic.
- Centralize DTO mapping in a single API layer.
- Standardize empty/loading/error skeleton states across pages.

## Testing Strategy
- Unit tests for pagination calculations and query-param synchronization.
- API client tests for feed/search/detail responses.
- Route smoke tests for `/articles` and `/feeds`.
- One integration test for article list paging behavior.

## Milestones
- Milestone A: App shell + routing + API client baseline.
- Milestone B: Articles list with search and pagination.
- Milestone C: Article detail page.
- Milestone D: Feeds page read-first placeholder.
- Milestone E: Activate management features when backend endpoints arrive.

## Risks and Mitigations
- Risk: endpoint gaps for feeds management.
  - Mitigation: explicitly stage these as disabled UI actions and placeholders.
- Risk: inconsistent payload fields in early projections.
  - Mitigation: defensive rendering and typed DTO normalizers.
- Risk: scope creep into full CMS behavior.
  - Mitigation: keep v1 read-first and admin-focused.

## Immediate Next Step
Start Milestone A in `src/frontend/briefly-admin` by scaffolding the app and implementing `/articles` with server-side paging first.
