# MedFlow frontend

React + TypeScript + Vite. Entry: `src/main.tsx`. The FastAPI server serves `dist/`
on port 8000. Development: `npm ci`, `npm run dev` (API proxy to port 8000).

## Language and appearance

The header offers Russian, Kazakh and English, plus a light/dark theme button.
The same controls are available on sign-in and administration screens. Choices
are saved locally in `medflow-display-preferences` and synchronize between tabs.
Changing language does not remount the workspace or reset forms and filters.
If browser storage is unavailable, preferences still work for the current visit.

UI messages live in `shared/lib/messages/`. Use `t(source, parameters)` at render
time; preserve Russian source keys in stored notices and module-level constants.
Dates, numbers and region labels follow the selected language. Source hospital
names and unmapped source categories remain unchanged, as do API identifiers and
model inputs. Exported PDF summaries remain in Russian, with a visible notice.
No external translation service receives hospital or account data.

Theme variables are in `app/styles/theme.css`; `dark.css` contains the remaining
scoped exceptions. Component colors keep the original light values as fallbacks.

## FSD boundaries

Imports go down: `app → pages → widgets → features → entities → shared`.
Separate slices on the same layer do not import each other. A slice exposes its
public API through `index.ts`; consumers must not reach into its internal files.
`npm run check:architecture` enforces these rules and runs as part of the build.

| Layer    | Responsibility                                                               |
| -------- | ---------------------------------------------------------------------------- |
| app      | Auth orchestration, routes, workspace state, global CSS cascade              |
| pages    | Page-specific requests/state and composition                                 |
| widgets  | Overview blocks, comparison, forecasts, workspace/public shell, admin panels |
| features | Referral filters, hospital selection, reviewed PDF export                    |
| entities | Hospital ID directory, region names, user presentation                       |
| shared   | Generic HTTP/CSRF/cancellation, wire DTOs, hooks, formatting, UI primitives  |

No ML inference, SQL or authorization rules in React. API contracts are in
`shared/api/types.ts` (wire DTOs, not duplicated domain models). Name-to-ID mapping
belongs to `entities/hospital`; the generic HTTP client does not know about hospitals.
Its lifecycle hooks clear the private directory when the account changes. The waiting
form sends a hospital ID explicitly; no special payload rewriting in HTTP.

Pages own their composition and state. Shared requests cancel stale responses;
forms keep their existing cancellation and version guards. Backend RBAC remains the
source of truth even when buttons or sections are hidden.

## Design and styles

The redesign covers the workspace shell, overview, public landing, sign-in and
administration. They share light clinical surfaces, restrained teal and flat layouts.
The 2026-09-29 composition adds a docked role-aware sidebar, an overview metric
rail next to the main chart, a narrow forecast configuration panel, a sign-in
portal and persistent admin section navigation. Existing light/dark palette
tokens, authentication, model inputs and API contracts are unchanged.

Referral filters have separate draft and applied states. Editing a date, region
or profile never triggers a request: submit **Apply** (or Enter) to commit the
whole draft. Reset returns to the dataset period and all regions/profiles.
`features/filter-referrals/model/filterDraft.ts` owns the date-order and reset
rules; pages receive the same filter feature through a composition slot.

`app/styles/index.css` defines the cascade; do not reorder imports casually. Theme
tokens are in `theme.css`. Overview-specific rules are scoped to `overview-layout`
and `overview-metrics`, without changing forecast or hospital metric layouts.
The 21st direction and constraints are recorded in `.21st/` (no private data).
The final `redesign.css` import owns the reversible composition layer and uses
existing semantic color variables only. It includes desktop, tablet and mobile
layouts. It does not duplicate data fetching or model logic.

## Local redesign rollback

The pre-redesign frontend was archived locally (not committed) under
`.runtime/backups/redesign-20260929.8KvY1ZcS/`. From the repository root:

```sh
bash .runtime/backups/redesign-20260929.8KvY1ZcS/restore.sh
```

This saves the current frontend before restoring the archive and rebuilding it.
No `.env`, PostgreSQL settings, backend, models or datasets are included or changed.
Reload the browser after rebuilding. The snapshot restores the whole frontend,
not just CSS; later frontend edits are retained in a fresh backup before rollback.

Short entrance animations live in `shared/lib/useEntrance.ts` and use the native
Web Animations API. Route/tab fades never remount forms. Motion is cancelled on
unmount and skipped for reduced-motion users; press feedback lives in `motion.css`.
No animation library, endless effects or number count-ups are used.

## Checks

```sh
npm run build
npm test
npm run format:check
```

Build checks FSD boundaries, TypeScript and production bundling. Existing tests
cover manual search, region filter values, reviewed PDF export, CSRF and cancellation.
Use a focused browser check for layout and interactions; no model retraining needed.

## Frontend updates

Production builds expose their asset names through `/api/frontend-version`. Open
tabs check on return/navigation and once per minute, and offer a manual reload
when code or styles have changed. HTML is served with `Cache-Control: no-store`.
No form is automatically discarded during an update.
