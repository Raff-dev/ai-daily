# AI Daily Orchestrator

You coordinate the AI Daily fleet pipeline. In this repository the deterministic Python runner performs orchestration, and this file documents the contract it enforces.

## Canonical flow

1. Establish the run date.
2. Run one section researcher per canonical section.
3. Store intermediate research packs under `.copilot-output/research/{run_date}/`.
4. Validate each research pack before synthesis.
5. Send all valid packs to the editor.
6. Validate the final English report against the research evidence.
7. Send the final English report to the translator.
8. Render stable HTML from JSON.

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

