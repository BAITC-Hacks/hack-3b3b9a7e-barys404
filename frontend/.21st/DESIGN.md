# MedFlow — design context

Working healthcare analytics, not a marketing page. Preserve the familiar flow:
overview → hospitals → comparison → forecasts. Roles and data scopes stay on the server.

Light surfaces, charcoal type, restrained teal. Plain navigation and a joined metric
ledger replace gradients, repeated cards and large uppercase labels. Charts and tables
have priority; glass is limited to the floating header. Motion makes transitions
visible: 560ms/18px lifts with 90ms stagger, 700–850ms chart reveals and 420ms
sliding tab indicators; no loops or number count-ups.

Tokens: `src/app/styles/theme.css`. Shared UI: `src/shared/ui`. Composition:
`src/pages/overview`, `src/widgets/overview`, `src/widgets/workspace-shell`.

Respect loading, empty, error and genuine zero states. Keep historical observations
separate from predictions. Region codes remain API values; names are presentation.

21st search references: App Dashboard Layout (28770), Advanced Stats (19070).
Used as layout inspiration only; existing React primitives reused. No catalog
component dependencies installed, no hosted AI generation, no private datasets sent.

Welcome, login and administration follow the same visual system. Public copy names
the actual functions instead of slogans. Login keeps the form prominent; admin
uses a compact account ledger and table. Public responsive rules belong to their
page styles, not duplicate overrides in readability.css.

Additional 21st search reference: minimal login (2428, ephraimduncan/login-2).
Used as structural inspiration only; no OAuth, animation or dependencies added.

Motion reference: 21st Reveal (19240, asanshay/reveal). Reused the reveal concept
with native Web Animations instead of installing a library. Shared implementation:
`src/shared/lib/useEntrance.ts`; reduced motion is respected, animation cleanup
runs on unmount/rapid navigation, and forms/data are never remounted for effects.

Stronger motion reference: Animated Tabs (24930, educalvolpz/animated-tabs).
Native sliding indicator reads its live position before interrupted transitions.
Chart clips and outcome bars reveal left-to-right using transforms, keeping real
values and keyboard interaction available. No additional dependencies installed.

Forecast refinement: use the overview's neutral surfaces, one hospital chooser
and the selected legal name repeated under the heading at the user's request,
task-specific headings and a full-width profile field. Result, basis/support and
validation error stay visible; detailed method explanations use native details.
Short hospital labels remove only legal prefixes, keeping all distinguishing
suffixes and untouched request names/IDs. Inspiration: Advanced Stats (19070),
with existing PageHeading, StatusPill, TrendChart and native controls reused.
The pre-change files are archived in .runtime/backups/forecast-ui-before-20260928.tar.gz.

Referral filters: group native date inputs under one period legend, with inline
start/end labels and shared outline; align date, region, profile and reset controls.
Keep valid date bounds and automatic range correction unchanged. Compact mobile
layout and all filter-specific responsive rules live in filters.css, not override
layers. 21st inspiration: Date Range Calendar in Dialog (25344); reuse only the
grouped-range concept, without installing a calendar or adding a modal.
