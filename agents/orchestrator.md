# AI Daily Orchestrator

You coordinate the AI Daily fleet pipeline. In this repository the deterministic Python runner performs orchestration, and this file documents the contract it enforces.

## Customization entry point

**`agents/coverage.md`** is the only file users need to edit. It defines the topics, sections, and search queries for the briefing. Edit it to change what the briefing covers — everything else stays the same.

## Canonical flow

1. Establish the run date.
2. Load the coverage brief from `agents/coverage.md`.
3. Run one compact section researcher per canonical section.
4. Store intermediate research packs under `.copilot-output/research/{run_date}/`.
5. Validate each research pack before synthesis.
6. Send all valid packs to the editor.
7. Validate the final English report against the research evidence.
8. Send the final English report to the translator.
9. Render stable HTML from JSON.

## Canonical sections

- `dev-tools`
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
- Keep breadth cheap: each researcher should find enough sources for 3 strong stories, not a fixed large source ledger.
