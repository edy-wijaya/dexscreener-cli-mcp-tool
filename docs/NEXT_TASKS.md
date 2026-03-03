# Next Build Tasks

Status key: `pending` | `in_progress` | `done`

## 1) Signal Quality - Early Runner Detection
- Status: `done`
- Scope:
  - Add volatility compression metric.
  - Add breakout readiness score.
  - Add boost velocity signal.
- Acceptance:
  - New runner board shows readiness/compression fields.
  - Scanner tags include at least one early-signal tag when criteria match.

## 2) Signal Quality - Relative Strength
- Status: `done`
- Scope:
  - Compute chain baseline for 1h momentum and flow.
  - Add per-token relative strength vs chain baseline.
- Acceptance:
  - New runner board shows RS field.
  - Rank/sort can prioritize RS.

## 3) Risk Control - Momentum Half-Life and Decay Filter
- Status: `done`
- Scope:
  - Track per-token momentum history during watch loops.
  - Estimate momentum half-life.
  - Filter fast-decay tokens with configurable thresholds.
- Acceptance:
  - CLI supports enabling/disabling decay filter.
  - Filter reason visible in tags/board hints.

## 4) Watch UX - Keyboard Interactions
- Status: `done`
- Scope:
  - Chain switching hotkeys (`1-9`).
  - Sort mode toggle (`s`).
  - Copy selected/top token + pair (`c`).
- Acceptance:
  - Footer shows active hotkeys and selected modes.
  - At least one interactive session demonstrates chain switch and sort mode updates.

## 5) Docs and Validation
- Status: `done`
- Scope:
  - README updates with new options/hotkeys.
  - Live command verification for `new-runners` and `new-runners-watch`.
- Acceptance:
  - Commands run successfully in current environment.
  - Output includes new analytics columns/panels.

## 6) Runner Noise Control
- Status: `done`
- Scope:
  - Raise default minimum liquidity for runner-oriented commands.
  - Add anti-thin filter (`max volume/liquidity ratio`).
- Acceptance:
  - `new-runners`, `new-runners-watch`, `alpha-drops`, and `alpha-drops-watch` expose the anti-thin option.
  - Near-zero-liquidity/highly thin candidates are filtered out by default.

## 7) Realtime Alpha Alert Guardrails
- Status: `done`
- Scope:
  - Add hard cap for alert send frequency in watch mode.
  - Keep cooldown-based alerting and risk gates.
- Acceptance:
  - `alpha-drops-watch` supports max alerts/hour.
  - Status panel explains when alert cap is hit.

## 8) Discovery and Top-New Reliability
- Status: `done`
- Scope:
  - Add search-seed discovery augmentation to improve multi-chain coverage.
  - Add 24h transaction filter/column for top-new scans.
- Acceptance:
  - Scanner ingests bounded search-based seeds.
  - `top-new` can filter by 24h txns and explains 1h `N/A` via recent inactivity.
