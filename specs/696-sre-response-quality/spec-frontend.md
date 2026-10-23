# Spec — 696 frontend phase: Quality view (soarplus-frontend-app1)

**Parent User Story**: Azure DevOps #696. ADO anchor: new Tasks under #696 (user decision 2026-10-19).
**Branch**: `feature/696-sre-response-quality` (same name, frontend repo; does not exist yet).
**Base contract**: C-01 quality-read-api (R1–R6, CR-001+CR-002 applied, pushed f34bf9c) and C-02
quality.view. This spec covers only the presentation increment in `soarplus-frontend-app1`; the API
phase has its own spec.md in this directory.

**Scope sentence (user-approved)**: a view with the catalog of evaluated targets and, on selecting
one, the evolution of the two quality metrics (last 5 points) with status and sample size.

## User scenarios

### US-F1 — Discover evaluated targets (P1)
An authorized user opens the Quality view and sees the catalog: one row per target with type,
name, profile, number of scored evaluations and its latest measurement (both metrics, date, status).

1. Given targets exist, when the view loads, then the catalog renders with the fields above,
   ordered as served (target_type, target), using R1 `{items,total}`; if total > page size the
   user can load more (paging per R1 limit/offset).
2. Given the catalog is empty, when the view loads, then an explicit empty state is shown (no error).
3. Given the API answers 401, the existing apiFetch refresh/login flow applies (no new handling).

### US-F2 — See the evolution of one target (P1)
*(amended by CR-003; delta approved 2026-10-20)*

Selecting a target opens a right-side modal drawer over the catalog and shows its last 5 evaluations
(newest first) as the two metric series with, per point: date, both metric values (0–1), sample size
(n), and measurement status. Evolution is not rendered inline below the catalog.

1. Given a selected target, when its history loads (R2), then a modal drawer contains up to 5 points
   in a chart (recharts, following daily-activity-chart conventions) plus a point list/table with
   status and n; `total` is shown so the user knows the full series size beyond the 5 shown.
2. Given a point with `status: null` (legacy, CR-002), then it is rendered as "unknown (legacy)"
   — never invented, never hidden.
3. Given a metric value null with `unavailable: true`, then the UI shows an explicit absence, not 0.
4. Given R2 answers 404 (no scored points), then a per-target empty state is shown.
5. Given R2 answers 409 (cross-type name collision), then the UI shows the API's Spanish detail
   as an error state for that target (no retry loop).
6. Given a scored point with `status: "judge_unavailable"`, any future unknown string, or the API
   sentinel `invalid_status`, then the UI preserves numeric metrics but marks the point explicitly as
   known/generic/invalid degraded in badge, tooltip and chart marker; it is never measured/green,
   legacy, hidden or converted to zero. *(CR-004; delta approved 2026-10-22.)*

### US-F3 — Only authorized users see the view (P1)
1. Given `is_admin === true` OR `effective_capabilities` (from GET /user/me) contains
   `quality.view`, then the Quality nav item is visible and the route renders.
2. Given neither holds, then the nav item is hidden and direct navigation to the route redirects
   to "/" (same pattern as /admin, admin/page.tsx:29-31).
3. Regardless of UI gating, a backend 403 on any quality call renders a "no access" state
   (backend remains the authority).

## Functional requirements

- **FR-F01**: New top-level route `/quality` (page in `src/app/quality/page.tsx`) and nav entry in
  `navItems` (sidebar.tsx), label "Quality". Standalone page, not a tab of an existing view.
- **FR-F02**: All API access goes through `src/lib/api.ts` (apiFetch) with new typed functions for
  R1, R2 and R5 (R6/R3/R4 not consumed in this increment); response types added to
  `src/lib/types.ts` mirroring the OpenAPI shapes, with `status: string | null` and
  `sample_sufficient: boolean | null` (CR-002).
- **FR-F03**: Gating per US-F3 using the existing session store user details; `UserDetails` type
  extended with `effective_capabilities: string[]` (field already served by /user/me; verified).
- **FR-F04**: Metric presentation uses R5 /quality/metrics descriptors (label, scale, polarity)
  instead of hardcoding metric names/semantics (spec FR-006 of the API phase).
- **FR-F05**: No credential-bearing field from /user/me is newly read, stored or displayed by this
  feature (only is_admin and effective_capabilities are consumed).
- **FR-F06**: Errors: reuse the toast convention (sonner) for unexpected errors; explicit inline
  states for empty catalog, 404 target, 409 collision and 403 no-access.
- **FR-F07**: No new runtime dependency (recharts, react-query, zustand, shadcn already present).
  No test framework is introduced in this increment.
- **FR-F08** *(added by CR-003; delta approved 2026-10-20)*: Evolution MUST render in a Quality-specific,
  right-side modal drawer built from the shared Radix/shadcn Dialog primitives and following the
  existing Playbook drawer presentation. Selecting a row opens it; closing by its close control,
  Escape or outside click clears the selection. The drawer MUST preserve every existing loading,
  empty, error, chart and table state, provide Dialog title/description semantics and contain its
  vertical and horizontal overflow. `PlaybookEditorDrawer` itself MUST NOT be reused because it is
  coupled to Playbook editing.
- **FR-F09** *(added by CR-004; delta approved 2026-10-22)*: Quality status MUST be typed
  `string | null` with explicit known branches plus a default. Catalog, point table, tooltip and
  chart MUST render `judge_unavailable` as known degraded, `invalid_status` as invalid degraded and
  every future unknown string as generic degraded, using accessible text and a distinct non-measured
  marker. Numeric values remain visible; metric null remains absence/gap; status null remains
  "unknown (legacy)".

## Success criteria

- **SC-F1**: With seeded dev data, the catalog and the per-target evolution render end-to-end
  against a local API with real data; legacy points (status null) visible — manual verification,
  recorded with screenshots or equivalent evidence.
- **SC-F2**: A user without quality.view and without admin never sees the nav item nor the view
  content (manual check with the synthetic local tokens / a custom role).
- **SC-F3**: `npm run lint` passes; `npm run build` succeeds.
- **SC-F4**: No response field outside the C-01 allow-list is displayed (the API already guarantees
  non-exposure; the UI adds no other source).
- **SC-F5** *(CR-004; delta approved 2026-10-22)*: Fixtures for `judge_unavailable`, a future
  unknown string and `invalid_status` are visibly degraded but retain numeric metrics; a null
  unavailable metric remains a gap/absence; a legacy-null point remains distinct, at desktop and
  narrow viewport.

## Out of scope (this increment)

R6 all-targets dashboard, R3/R4 evaluation-detail and cases drill-down, comparisons/alerts
(FR-017 API phase), test-framework introduction, any soarplus-api change.

## Assumptions and verified facts

- Verified (696-frontend-2): Next 16 App Router SPA, react-query 5.90, recharts 3.8.1 in use,
  apiFetch with 401-refresh, nav pattern, admin hide/redirect pattern, no test framework,
  branch absent in frontend repo.
- Verified (696-api-20): /user/me serves effective_capabilities + is_admin; gate parity;
  /rbac/* is admin-only; no other capability endpoint.
- Assumed: dev data remains readable during implementation validation (read-only local API).

## Dependency note

Plan-level merge dependency stands: soarplus-api merges before frontend implements against C-01
(or the user explicitly accepts implementing against the pushed feature branch). To be resolved at
the frontend plan gate (Gate 2).

## Gate 1 (specification)

> Gate: specification approved by user on 2026-10-19 (admiral session), as drafted (standalone
> /quality page; R1+R2+R5; no test framework this increment).

## Amendments

- **CR-003 (2026-10-20, APPROVED)** — previous US-F2 presentation: selecting a
  target showed Evolution in the page's inline master-detail area below the catalog. New wording
  moves the same content and states to a lateral modal drawer; FR-F08 records overlay, close,
  accessibility and overflow behaviour. No data or authorization contract changes.
- **CR-004 (2026-10-22, APPROVED, revised)** — changes Quality status to open `string|null` and
  requires known, future-unknown and invalid-sentinel degraded rendering while preserving numeric,
  metric-null and legacy-status-null semantics. Previous behavior typed only five statuses and
  rendered an unknown runtime literal as a generic solid point.

> Gate: delta approved by user on 2026-10-20 (CR-003).
>
> Gate: revised delta approved by user on 2026-10-22 (CR-004), covering open status strings,
> `invalid_status` and degraded/default frontend rendering.
