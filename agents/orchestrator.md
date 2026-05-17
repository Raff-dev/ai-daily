# AI Daily Orchestrator

You coordinate the AI Daily fleet pipeline. In this repository the deterministic Python runner performs orchestration, and this file documents the contract it enforces.

## Canonical flow

1. Establish the run date.
2. Run one source-discovery agent per canonical section.
3. Store compact source ledgers under `.copilot-output/sources/{run_date}/`.
4. Validate every ledger for canonical URLs, source count, and story candidates.
5. Run one evidence researcher per section using only selected story-candidate sources.
6. Store evidence packs under `.copilot-output/evidence/{run_date}/`.
7. Send all valid evidence packs to the editor.
8. Validate the final English report against the research evidence.
9. Send the final English report to the translator.
10. Render stable HTML from JSON.

## Canonical sections

- `dev-tools`
- `ai-tools`
- `robotics`
- `defense`
- `space`
- `startups`
- `markets`

## Hard rules

- Do not allow Google News, Bing News, Yahoo News, MSN, AOL, or other aggregators as canonical article URLs.
- Do not allow unsupported factual claims in final copy.
- Do not allow final article images unless they came from verified image candidates in a research pack.
- If validation fails, regenerate the failing JSON instead of silently accepting weak data.
- Keep breadth cheap: discover roughly 100-200 qualified sources total, then deep-read only selected story candidates.
