# AI Daily Orchestrator

You coordinate the AI Daily fleet pipeline. In this repository the deterministic Python runner performs orchestration, and this file documents the contract it enforces.

## Customization entry point

**`agents/coverage.md`** is the only file users need to edit. It defines the topics, sections, and search queries for the briefing. Edit it to change what the briefing covers — everything else stays the same.

## Canonical flow

1. Establish the run date.
2. Load the coverage brief from `agents/coverage.md`.
3. Run the deterministic Python source collector per canonical section.
4. Store compact source ledgers under `.copilot-output/sources/{run_date}/`.
5. Validate every ledger for canonical URLs, source count, and story candidates.
6. Run one evidence researcher per section using only selected story-candidate sources.
7. Store evidence packs under `.copilot-output/evidence/{run_date}/`.
8. Send all valid evidence packs to the editor.
9. Validate the final English report against the research evidence.
10. Send the final English report to the translator.
11. Render stable HTML from JSON.

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
- Keep breadth cheap: discover roughly 100-200 qualified sources total with code, then deep-read only selected story candidates with agents.
