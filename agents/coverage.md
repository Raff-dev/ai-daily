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

Per section, prefer these primary sources before falling back to general outlets:

- `dev-tools`: GitHub Blog/Changelog, OpenAI, Anthropic, Microsoft/Copilot, Cursor, Windsurf, Sourcegraph, JetBrains, Hacker News, GitHub Trending, Product Hunt
- `robotics`: IEEE Spectrum, The Robot Report, Boston Dynamics, Figure, Tesla Optimus, NVIDIA Robotics, Agility, Unitree
- `defense`: DefenseScoop, Breaking Defense, Defense One, DoD/DARPA/DIU releases, Anduril, Palantir, Shield AI, Helsing, NATO/EU releases
- `space`: SpaceNews, NASA, ESA, SpaceX, Rocket Lab, Planet, Maxar, Blue Origin, launch livestreams
- `startups`: TechCrunch, The Information, Crunchbase, YC, a16z, Sequoia, Index, company launch posts, Product Hunt
- `markets`: Reuters, Bloomberg, CNBC, WSJ, FT, SEC filings, earnings releases, investor relations pages

## How to use this file when topics ARE user-provided

If the user named their own topics (e.g. "Polish news, football, motorization,
climbing"), do **not** use these defaults. Instead:

1. Map each topic to one section (3-6 sections total)
2. Use the same shape — `id`, `color`, `icon`, `badge`, search queries, source map
3. Pick sensible colors and Lucide icons that fit the topic
4. Pick primary sources you would trust for each topic (official sites, established outlets)

The structure stays the same; only the content changes.
