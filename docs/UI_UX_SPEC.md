# UI/UX Specification (Terminal)

## Design Principles
1. Fast visual parsing over decorative output.
2. Consistent color semantics:
   - Green: positive momentum
   - Red: negative momentum
   - Cyan/Blue: structure/meta
   - Magenta: signals/tags
3. Keep primary table visible as the anchor.
4. Show secondary summaries in compact side/bottom panels.

## Primary Views
1. `hot`:
   - Static ranked table.
2. `watch`:
   - Full-screen board with refresh status.
3. `inspect`:
   - Detail panel + risk/proxy panel.
4. `search`:
   - Lightweight table for quick lookup.

## Board Layout (Watch / Enhanced Hot)
1. Top:
   - Product title and UTC timestamp.
2. Middle:
   - Hot Runner leaderboard.
3. Bottom:
   - Chain heat panel.
   - Market structure/risk panel.
   - Footer status (refresh interval, filters, API health hints).

## Leaderboard Columns
1. Rank
2. Chain
3. Token + score
4. Price
5. 1h change
6. 24h volume
7. 1h txns
8. Liquidity
9. Market cap
10. Boost count/amount
11. Age
12. Signal tags

## Readability Rules
1. Use compact number formats (`K/M/B`).
2. Truncate long token names safely.
3. Avoid non-ASCII assumptions for JSON output.
4. Ensure content remains legible at 100-column terminals.

## Interaction Model
1. Non-interactive commands are script-first.
2. Watch mode is Ctrl+C driven.
3. Tasks system commands should be explicit and single-purpose:
   - create, list, show, update-status, run.

## Error UX
1. Fail with a clear one-line reason.
2. Suggest next command when possible.
3. Keep stack traces hidden by default for user commands.

## Accessibility Notes
1. Color should not be the only signal:
   - include +/- symbols
   - include textual tags
2. JSON mode should preserve full numeric values for downstream tooling.

## UI Acceptance Criteria
1. Hot table renders cleanly without wrapped corruption in standard terminal widths.
2. Watch mode updates without flicker artifacts and no duplicate scroll spam.
3. Inspect view clearly separates facts and inferred distribution proxies.
