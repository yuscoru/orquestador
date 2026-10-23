# Plan — 696 frontend phase: Quality view (soarplus-frontend-app1)

Derives from spec-frontend.md (Gate 1 approved 2026-10-19). All repository facts verified in
analysis 696-frontend-2 unless marked otherwise.

## 1. Architecture fit

*(amended by CR-003; delta approved 2026-10-20)*

SPA App Router page, client-rendered like every existing view. Catalog plus modal detail: the page
owns selection, open/close state and the dependent history query (`enabled: hydrated && !!selected`),
while a Quality-specific drawer presents the existing Evolution states over the catalog.

```
/quality (src/app/quality/page.tsx, "use client")
   ├── CatalogTable        R1 useQuery ["quality-targets", limit, offset]
   ├── QualityEvolutionDrawer (Radix Dialog, right-side/full-height)
   │     └── TargetEvolution R2 useQuery ["quality-history", target] (enabled on selection)
   │           ├── EvolutionChart (recharts LineChart, 2 series; CR-004 degraded marker)
   │           └── PointsTable (date, metrics, n, open-string status:
   │                            null legacy; known/future/invalid degraded)
   └── metrics descriptors R5 useQuery ["quality-metrics"]
```

The drawer reuses `src/components/ui/dialog.tsx` and the positioning/presentation pattern evidenced
in `PlaybookEditorDrawer`; it does not reuse the Playbook editor component or its form/dirty/save
semantics. Closing clears selection. No Evolution card remains in normal page flow.

## 2. Touch list (complete)

| File | Change |
|---|---|
| `src/lib/types.ts` | + Quality types; CR-004 changes status to `string|null` with known/default classification while null remains legacy; `UserDetails` + `effective_capabilities: string[]` |
| `src/lib/api.ts` | + `getQualityTargets(limit, offset)`, `getQualityTargetEvaluations(target)`, `getQualityMetrics()` via apiFetch |
| `src/app/quality/page.tsx` | page: gating, catalog, selection/history ownership; CR-003 removes inline Evolution and controls the overlay |
| `src/components/ui/quality-*.tsx` | catalog table, evolution chart, points table; CR-003 adds a Quality-specific Evolution drawer using shared Dialog primitives |
| `src/components/layout/sidebar.tsx` | + navItem "Quality" (conditional render per gating rule) |
| `src/components/layout/header.tsx` or session store | no change expected: /user/me already fetched; only the type gains the field |

Nothing else. No new dependency, no api.ts refactor, no admin page change.

## 3. Contracts

| Contract | Direction | Notes |
|---|---|---|
| C-01 quality-read-api (R1, R2, R5) | consumes | Authority: generated OpenAPI of soarplus-api (f34bf9c). R2 semantics: ≤5 desc, total = full series, 404/409 |
| C-02 quality.view | consumes | UI rule `is_admin \|\| effective_capabilities.includes("quality.view")`; backend 403 remains authority |
| GET /user/me `effective_capabilities` | consumes (existing) | Verified served today (models.py:237-241); additive type extension in UI only |

Provides: none. No api change in this phase.

## 4. Decisions

- **D-F1 Gating UX**: hide nav item + redirect on direct navigation (admin pattern) + inline
  "no access" state on backend 403. No "disabled" rendering.
- **D-F2 Paging UX**: catalog uses R1 defaults (limit 100); "load more" button appears only when
  items.length < total. No URL-state for paging (consistent with existing views).
- **D-F3 Chart**: one chart, two lines (both metrics 0–1 on one axis), points carry status in
  tooltip; legacy (status null) points rendered with a distinct marker. Table below the chart is
  the authoritative detail (chart is illustrative).
- **D-F4 Merge dependency**: plan dependency "api merges first" — TO BE RESOLVED AT THIS GATE:
  (option 1) wait for api PR+merge; (option 2) user accepts implementing against the pushed
  feature branch f34bf9c (API shape risk ~zero: contract validated live; risk is process-level,
  rebase/rework if api changes before merge).
- **D-F5 Validation without test framework** (spec FR-F07): `npm run lint` + `npm run build` +
  scripted manual pass against the read-only local API with real dev data (checklist in tasks),
  evidence recorded in the worker's checkpoint. The quality integration script (api repo) remains
  the contract-side safety net.
- **D-F6 Open status classification** *(CR-004; delta approved 2026-10-22)*: measured is normal;
  status null is legacy; `judge_unavailable` is known degraded; `invalid_status` is invalid degraded;
  every other unknown string is generic degraded. Preserve served numeric values but use accessible
  warning/degraded badge/marker/note; preserve metric-null gaps and never invent zero.

## 5. Risks

| id | Risk | Mitigation |
|---|---|---|
| RF-1 | node_modules absent in checkout; install needed before lint/build | `npm ci` from lock (verified lock present); record install output |
| RF-2 | /user/me type drift (UI type vs API) | Type mirrors verified response; gate rule tested manually with the 3 synthetic tokens |
| RF-3 | Chart readability with ≤5 points and nulls | Table is authoritative (D-F3); explicit absence rendering |
| RF-4 | CORS/local API during manual validation | audited `run_api_local_ui.py` sets the exact localhost origin (verified in runbook) |
| RF-5 | Known/future/invalid statuses can carry numeric scores but are not necessarily fully measured | Preserve numbers, classify with default degraded branch; do not infer checkpoint or promotion |

## 6. Execution shape (preview for tasks)

Original frontend increment: single worker (frontend), branch creation, types+api functions, page+
components, nav+gating, manual validation checklist, lint+build, commit (no push without Gate 4).

CR-003 adds one frontend-only CHANGE assignment: move the existing Evolution composition into a
Quality-specific Dialog/drawer, then validate interaction, responsive overflow, accessibility
semantics, unchanged data/error states, lint and build. No API ordering dependency is added.

CR-004 (delta approved 2026-10-22) adds an API→frontend contract dependency: API first publishes
nullable open string plus safe invalid sentinel and regressions; frontend then updates its type/shared
known+default classification, badges and chart degraded marker/note, followed by lint/build/browser
evidence. No page/query/RBAC change.

## Gate 2 (plan)

> Gate: plan approved by user on 2026-10-19 (admiral session). D-F4 resolved as OPTION 2: implement
> now against the pushed feature branch (f34bf9c on origin); the user explicitly accepts the
> process-level risk (rebase/rework if soarplus-api changes before its merge).
