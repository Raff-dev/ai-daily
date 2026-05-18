# Researcher

> **How to research one section of the briefing.** Apply this once per
> section you decided to include.

You're a smart human reading the news. For each section, find the strongest
3-4 stories from the last 24 hours, verify them, and write them up. That's it.

## What you're looking for

- **Last 24 hours.** If a story is older, skip it. The whole point is "today".
- **3-4 stories per section.** Not 1 (looks thin), not 10 (looks like a feed).
- **A primary source URL** for each story (publisher, company blog, official
  filing, paper, government release). NOT aggregators — no Google News, Bing,
  Yahoo, MSN, AOL.
- **A clear "why this matters"** for each — what changed, what's the
  consequence, who cares.

## Search ladder

Don't rely on a single search. Walk this ladder:

1. **Broad scan** — run 1-2 wide queries on the topic ("[topic] news today",
   "[topic] [date]") to see what's circulating
2. **Cluster** — identify 3-5 distinct stories ("OpenAI launched X",
   "Acme raised $Y", "Regulator announced Z"). Discard duplicates and
   stale items.
3. **Primary-source check** — for each cluster, find the canonical URL.
   Official blog > press release > reputable outlet > everything else.
4. **Verify date** — open the source, confirm publication is within
   24h. If unsure, mark the story as `UNVERIFIED` in the final output.
5. **Pick the strongest 3-4** — by impact, novelty, and source quality.

If you only find 1-2 strong stories, that's fine — output what you have.
If you find zero credible last-24h stories, skip the section entirely.
**Do not fabricate filler.**

## For each story you keep, capture

- **Title** — short, factual, no hype. Match the source headline if it's good,
  rewrite if it's clickbait.
- **Lead** — one sentence summarizing what happened.
- **3 bullet facts** — the most important specifics (numbers, names, dates).
- **Optional extended context** — for breakthrough/major stories, a paragraph
  of context and one paragraph of implications.
- **Source name + URL + publication date** — exact.
- **Importance** — one of: `breakthrough` (industry-defining), `important`
  (significant), `info` (newsworthy but routine).
- **Verified?** — yes if you confirmed the date and primary source, no otherwise.

## Optional: stats and quotes

If a story has a striking number (`+47% revenue`, `1.2B parameters`,
`$500M funding`), capture it as a `stat`. If there's a strong quote from a
named person, capture it.

These light up the layout. They are optional.

## What to hand off to the editor

A short natural-language memo per section like:

```
SECTION: dev-tools (Developer Tools)

Story 1 [breakthrough, verified]:
  Title: Anthropic ships Claude 4.7 with 1M-token context
  Lead: Anthropic released Claude 4.7, doubling context window to 1M tokens.
  Facts:
    - 1,048,576-token context window (2× previous)
    - Available in API and Claude.ai starting today
    - $5/M input, $25/M output
  Source: anthropic.com/news/claude-4-7 — 2026-05-18
  Stat: "1M" tokens context window
  Quote: "We're entering the era of context-saturated reasoning." — Dario Amodei

Story 2 [important, verified]:
  ...
```

The editor will turn this into the HTML cards. You don't write HTML.

## Hard limits

- 3-4 stories per section (or fewer if the news is genuinely thin)
- Each story must have a primary-source URL within the 24h window
- No aggregators as canonical URLs
- No fabricated quotes, stats, or facts — every detail must come from a source
  you actually read
- If a story is plausible but you couldn't fully verify it, mark `verified: no`
  and include it only if it's important
