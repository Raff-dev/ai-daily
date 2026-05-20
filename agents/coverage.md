# Default coverage

> **Used when the user didn't name their own topics.** If they did, ignore
> this file and follow what they asked for.

This file defines the **default briefing** — what topics to cover, what to
search for, what makes a good source. The maintainer of this fork can edit
it freely. Beginners: this is the file to change when you want a different
default.

## Default topics

Search for important news from the **last 24 hours** about:

1. AI developer tools — Claude, Anthropic, Copilot, Cursor, Codex, Windsurf, coding agents
2. Robotics, humanoid robots, drones, embodied AI
3. Defense, military AI, autonomous weapons, security policy
4. Space — NASA, SpaceX, satellites, astronautics, AI in space operations
5. AI startup funding, acquisitions, launches, product announcements
6. AI-related market moves — only on a major event (>5% price swing, earnings,
   major partnership, product launch, regulatory action)

## Default sections

| Section | `id` | Color | Icon | Badge |
|---|---|---|---|---|
| Developer Tools | `dev-tools` | `#2563EB` | `monitor` | `DEV` |
| Robotics | `robotics` | `#16A34A` | `bot` | `BOT` |
| Defense | `defense` | `#DC2626` | `shield` | `DEF` |
| Space | `space` | `#7C3AED` | `rocket` | `ORB` |
| Startups | `startups` | `#EA580C` | `banknote` | `CAP` |
| Markets *(only on major events)* | `markets` | `#0F766E` | `bar-chart-2` | `MKT` |

## Default search queries

Use these as starting points. Replace `{DATE}`, `{YEAR}`, `{MONTH}` with today's values.

1. `"Claude OR Anthropic OR Copilot OR Cursor OR Codex OR Windsurf AI coding news {DATE} {YEAR}"`
2. `"humanoid robot drone AI news {DATE} {YEAR}"`
3. `"AI military defense autonomous weapons news {DATE} {YEAR}"`
4. `"AI space NASA SpaceX astronautics news {DATE} {YEAR}"`
5. `"AI startup funding investment Series {DATE} {YEAR}"`
6. `"Nvidia Meta Tesla Microsoft Google Apple stock AI news today {DATE}"`

## Default source preferences

Per section, prefer the **scrape-friendly** sources listed first. When two
outlets cover the same story, choose the one that returns a clean
`og:image` and full article HTML without bot-protection — that keeps card
preview images intact in the final briefing.

**Scrape-friendly (preferred):**

- `dev-tools`: official company blogs first — Anthropic (anthropic.com / claude.com), OpenAI, GitHub Blog & Changelog, Cursor, Windsurf, Sourcegraph, JetBrains — then TechCrunch, The Verge, Ars Technica, Hacker News, Product Hunt, GitHub Trending
- `robotics`: IEEE Spectrum, The Robot Report, Robotics & Automation News, Boston Dynamics, Figure, Tesla Optimus, NVIDIA Robotics, Agility, Unitree, Apptronik official posts
- `defense`: DefenseScoop, Defense One, War on the Rocks, Military Times, Military Embedded Systems, DoD/DARPA/DIU official releases, Anduril, Palantir, Shield AI, Helsing official blogs
- `space`: SpaceNews, NASA, ESA, Spaceflight Now, Ars Technica space, The Verge space, SpaceX, Rocket Lab, Planet, Maxar, Blue Origin official
- `startups`: TechCrunch, The Verge, SiliconANGLE, Tech Startups, HIT Consultant (vertical), YC blog, a16z blog, Sequoia, Index, company launch posts, Product Hunt
- `markets`: SEC filings, company investor-relations pages, earnings releases hosted on company sites, Tom's Hardware, The Motley Fool, MarketWatch

**Use with caution (often block scrapers — go through Microlink for og:image):**

- `defense`: Breaking Defense (blocks direct curl)
- `markets`: CNBC, WSJ, FT, Bloomberg, Reuters (paywall / bot-protection)
- `startups`: PR Newswire, BusinessWire (anti-scrape stub)
- `stocks/companies`: StockTitan (anti-scrape)

When a story has only "blocked" sources, the editor's image fallback chain
will handle it via Microlink — but if you can credibly substitute a
scrape-friendly outlet covering the same event, prefer that as the
primary URL in the card.

## How to use this file when topics ARE user-provided

If the user named their own topics (e.g. "Polish news, football, motorization,
climbing"), do **not** use these defaults. Instead:

1. Map each topic to one section (3-6 sections total)
2. Use the same shape — `id`, `color`, `icon`, `badge`, search queries, source map
3. Pick sensible colors and Lucide icons that fit the topic
4. Pick primary sources you would trust for each topic (official sites, established outlets)

The structure stays the same; only the content changes.
