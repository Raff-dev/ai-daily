#!/usr/bin/env python3
"""AI Daily Brief — generates a daily AI news HTML report using Claude."""

import anthropic
import os
from datetime import datetime
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo  # Python < 3.9


SYSTEM_PROMPT = """\
You are an AI News Specialist. Your task is to generate a daily AI Daily Brief — \
a complete, self-contained HTML file covering AI world events from the last 24 hours.

## STEP 1 — Searches

Use web_search for each of the following queries (replace {DATE} with today's date, \
{YEAR} with the year, {MONTH} with the month):

1. "Claude OR Anthropic OR Copilot OR Cursor OR Codex OR Windsurf AI coding news {DATE} {YEAR}"
2. "humanoid robot drone AI news {DATE} {YEAR}"
3. "AI military defense autonomous weapons news {DATE} {YEAR}"
4. "AI space NASA SpaceX astronautics news {DATE} {YEAR}"
5. "AI startup funding investment Series {DATE} {YEAR}"
6. "Nvidia Meta Tesla Microsoft Google Apple stock AI news today {DATE}"
7. "AI stock emerging company IPO {MONTH} {YEAR}"
8. "energy AI data center power nuclear stock news {DATE} {YEAR}"

## STEP 2 — Filtering

Keep only articles published in the last 24 hours. For each section select max 4 most \
important stories. Add the Markets section ONLY if: price change >±5%, earnings report, \
or a major announcement. Skip any topical section with no last-24h news.

## STEP 3 — Verification

For each story: verify the publication date. Prefer Tier 1 sources (anthropic.com, \
openai.com, techcrunch.com, crunchbase.com, defenseone.com, ieee.org, space.com, \
spaceflightnow.com, nvidianews.nvidia.com). Mark unverified stories as [UNVERIFIED].

## STEP 4 — Generate HTML

Generate a complete HTML file matching the specification below.

### HTML Template:

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Daily — {DATE_LONG} · Extended Edition</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<script src="https://unpkg.com/lucide@latest/dist/umd/lucide.min.js"></script>
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }
body { font-family: 'Inter', system-ui, sans-serif; font-size: 15px; line-height: 1.65; color: #111827; background: #F3F4F6; -webkit-font-smoothing: antialiased; }
:root {
  --bg-page: #F3F4F6; --bg-card: #FFFFFF; --text-primary: #111827; --text-secondary: #374151; --text-muted: #6B7280;
  --border: #E5E7EB; --border-strong: #D1D5DB;
  --shadow-sm: 0 1px 3px rgba(0,0,0,.08); --shadow-md: 0 4px 12px rgba(0,0,0,.08);
  --radius: 12px; --radius-sm: 8px; --radius-pill: 9999px;
  --dev: #2563EB; --dev-bg: #EFF6FF; --dev-border: #BFDBFE;
  --robot: #16A34A; --robot-bg: #F0FDF4; --robot-border: #BBF7D0;
  --defense: #DC2626; --defense-bg: #FEF2F2; --defense-border: #FECACA;
  --space: #7C3AED; --space-bg: #F5F3FF; --space-border: #DDD6FE;
  --startup: #EA580C; --startup-bg: #FFF7ED; --startup-border: #FED7AA;
  --market: #0F766E; --market-bg: #F0FDFA; --market-border: #99F6E4;
}
[data-lucide] { width: 14px; height: 14px; stroke-width: 2; display: inline-block; vertical-align: -2px; flex-shrink: 0; }
.section-icon [data-lucide] { width: 20px; height: 20px; stroke-width: 1.75; }
.badge [data-lucide] { width: 11px; height: 11px; stroke-width: 2.5; vertical-align: -1px; }
.card-image-placeholder [data-lucide] { width: 48px; height: 48px; stroke-width: 1.25; color: #C4C9D4; }
.masthead-nav a [data-lucide] { width: 13px; height: 13px; }
.footer-title [data-lucide] { width: 15px; height: 15px; vertical-align: -3px; }
.sources-section h4 [data-lucide] { width: 12px; height: 12px; }
.footer-meta p [data-lucide] { width: 12px; height: 12px; }
.breaking-tag [data-lucide] { width: 10px; height: 10px; stroke-width: 2.5; vertical-align: -1px; }
.implications [data-lucide] { width: 14px; height: 14px; vertical-align: -2px; }
.bullet-list li [data-lucide] { width: 13px; height: 13px; vertical-align: -2px; margin-right: 2px; }
.stock-change [data-lucide] { width: 14px; height: 14px; vertical-align: -3px; }
.card-image-placeholder { font-size: 0; }
.page-wrapper { max-width: 1180px; margin: 0 auto; padding: 0 16px 60px; }
.masthead { background: #fff; border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 100; box-shadow: var(--shadow-sm); }
.masthead-inner { max-width: 1180px; margin: 0 auto; padding: 0 16px; display: flex; align-items: center; gap: 24px; height: 56px; }
.masthead-brand { display: flex; align-items: baseline; gap: 10px; flex-shrink: 0; }
.masthead-title { font-size: 22px; font-weight: 800; letter-spacing: -0.03em; color: #111827; }
.masthead-edition { font-size: 11px; font-weight: 500; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.08em; }
.masthead-nav { display: flex; gap: 4px; flex: 1; overflow-x: auto; scrollbar-width: none; }
.masthead-nav::-webkit-scrollbar { display: none; }
.masthead-nav a { display: flex; align-items: center; gap: 5px; padding: 5px 12px; border-radius: var(--radius-pill); font-size: 12px; font-weight: 500; color: var(--text-secondary); text-decoration: none; white-space: nowrap; transition: background 0.15s; }
.masthead-nav a:hover { background: var(--bg-page); }
.masthead-version { flex-shrink: 0; padding: 4px 12px; background: #111827; color: #fff; border-radius: var(--radius-pill); font-size: 11px; font-weight: 600; }
.hero-header { background: linear-gradient(135deg, #111827 0%, #1e3a5f 100%); color: white; padding: 48px 16px 40px; margin-bottom: 28px; }
.hero-inner { max-width: 1180px; margin: 0 auto; }
.hero-date { font-size: 12px; font-weight: 500; color: #93C5FD; text-transform: uppercase; letter-spacing: 0.12em; margin-bottom: 10px; }
.hero-title { font-size: 42px; font-weight: 800; letter-spacing: -0.04em; line-height: 1.05; margin-bottom: 12px; }
.hero-title span { color: #60A5FA; }
.hero-tagline { font-size: 15px; color: #9CA3AF; max-width: 480px; line-height: 1.6; margin-bottom: 24px; }
.hero-stats { display: flex; gap: 32px; flex-wrap: wrap; }
.hero-stat-num { font-size: 28px; font-weight: 700; color: #fff; letter-spacing: -0.03em; display: block; }
.hero-stat-label { font-size: 11px; color: #6B7280; font-weight: 500; text-transform: uppercase; letter-spacing: 0.08em; }
.breaking-banner { background: #FEF2F2; border: 1px solid #FECACA; border-radius: var(--radius-sm); padding: 10px 16px; margin-bottom: 24px; display: flex; align-items: center; gap: 10px; font-size: 13px; font-weight: 500; color: #991B1B; }
.breaking-tag { background: #DC2626; color: white; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 700; letter-spacing: 0.1em; flex-shrink: 0; display: inline-flex; align-items: center; gap: 4px; }
.news-section { margin-bottom: 36px; }
.section-header { display: flex; align-items: center; gap: 12px; padding: 12px 16px; background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius) var(--radius) 0 0; margin-bottom: 2px; }
.section-icon { font-size: 0; line-height: 1; }
.section-meta { flex: 1; }
.section-overline { display: block; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.12em; color: var(--text-muted); margin-bottom: 1px; }
.section-title { font-size: 16px; font-weight: 700; color: var(--text-primary); letter-spacing: -0.01em; }
.section-count { font-size: 11px; font-weight: 600; color: var(--text-muted); background: var(--bg-page); border: 1px solid var(--border); padding: 3px 10px; border-radius: var(--radius-pill); }
.section-divider { height: 3px; border-radius: 0 0 3px 3px; margin-bottom: 12px; }
.articles-grid { display: grid; grid-template-columns: repeat(12, 1fr); gap: 12px; }
.news-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); display: flex; flex-direction: column; overflow: hidden; transition: box-shadow 0.15s, transform 0.15s; box-shadow: var(--shadow-sm); }
.news-card:hover { box-shadow: var(--shadow-md); transform: translateY(-1px); }
.news-card.featured { grid-column: span 7; }
.news-card.secondary { grid-column: span 5; }
.news-card.standard { grid-column: span 6; }
.news-card.full { grid-column: span 12; }
.card-image-placeholder { width: 100%; aspect-ratio: 16/7; background: linear-gradient(135deg, #F3F4F6, #E5E7EB); display: flex; align-items: center; justify-content: center; }
.card-body { padding: 16px 18px; flex: 1; display: flex; flex-direction: column; }
.card-tags { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin-bottom: 10px; }
.badge { display: inline-flex; align-items: center; gap: 4px; padding: 3px 9px; border-radius: var(--radius-pill); font-size: 10.5px; font-weight: 600; letter-spacing: 0.04em; text-transform: uppercase; line-height: 1; white-space: nowrap; }
.badge-dev     { background: var(--dev-bg);     color: var(--dev);     border: 1px solid var(--dev-border); }
.badge-robot   { background: var(--robot-bg);   color: var(--robot);   border: 1px solid var(--robot-border); }
.badge-defense { background: var(--defense-bg); color: var(--defense); border: 1px solid var(--defense-border); }
.badge-space   { background: var(--space-bg);   color: var(--space);   border: 1px solid var(--space-border); }
.badge-startup { background: var(--startup-bg); color: var(--startup); border: 1px solid var(--startup-border); }
.badge-market  { background: var(--market-bg);  color: var(--market);  border: 1px solid var(--market-border); }
.badge-breakthrough { background: #F5F3FF; color: #7C3AED; border: 1px solid #DDD6FE; }
.badge-important    { background: #FFFBEB; color: #D97706; border: 1px solid #FDE68A; }
.badge-info         { background: #F9FAFB; color: #6B7280; border: 1px solid #E5E7EB; }
.badge-unverified   { background: #FFF7ED; color: #C2410C; border: 1px solid #FED7AA; }
.article-title { font-size: 17px; font-weight: 700; line-height: 1.3; color: var(--text-primary); margin-bottom: 8px; letter-spacing: -0.02em; }
.news-card.featured .article-title { font-size: 21px; }
.article-deck { font-size: 13.5px; color: var(--text-secondary); line-height: 1.55; margin-bottom: 14px; font-style: italic; }
.bullet-list { list-style: none; margin-bottom: 14px; display: flex; flex-direction: column; gap: 6px; }
.bullet-list li { font-size: 13.5px; color: var(--text-secondary); line-height: 1.55; padding-left: 14px; position: relative; }
.bullet-list li::before { content: '•'; position: absolute; left: 0; color: var(--text-muted); font-weight: 700; }
.bullet-list strong { color: var(--text-primary); font-weight: 600; }
.stat-row { display: flex; flex-wrap: wrap; margin-bottom: 12px; }
.stat-highlight { display: inline-flex; align-items: baseline; gap: 4px; padding: 6px 12px; background: var(--bg-page); border: 1px solid var(--border); border-radius: var(--radius-sm); margin: 4px 4px 4px 0; }
.stat-number { font-size: 22px; font-weight: 700; letter-spacing: -0.03em; color: var(--text-primary); }
.stat-label { font-size: 11px; color: var(--text-muted); font-weight: 500; }
.extended-content { border-top: 1px solid var(--border); margin-top: 12px; padding-top: 12px; }
.body-text { font-size: 14px; color: var(--text-secondary); line-height: 1.68; margin-bottom: 10px; }
.implications { background: #FAFAF9; border-left: 3px solid #D1D5DB; padding: 8px 12px; border-radius: 0 var(--radius-sm) var(--radius-sm) 0; font-size: 13.5px; color: var(--text-secondary); }
.article-quote { border-left: 3px solid var(--border-strong); margin: 12px 0; padding: 8px 14px; }
.article-quote p { font-style: italic; font-size: 15px; color: var(--text-primary); line-height: 1.5; margin-bottom: 4px; }
.article-quote cite { font-size: 11.5px; color: var(--text-muted); font-style: normal; font-weight: 500; }
.card-footer { margin-top: auto; padding-top: 12px; border-top: 1px solid var(--border); display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.source-link { display: inline-flex; align-items: center; gap: 5px; text-decoration: none; font-size: 12px; font-weight: 500; color: #2563EB; padding: 4px 10px; background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: var(--radius-pill); transition: background 0.12s; }
.source-link:hover { background: #DBEAFE; }
.source-link img { width: 12px; height: 12px; border-radius: 2px; }
.pub-time { font-size: 11.5px; color: var(--text-muted); margin-left: auto; }
.funding-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; margin-bottom: 12px; }
.funding-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 14px 16px; box-shadow: var(--shadow-sm); }
.funding-amount { font-size: 26px; font-weight: 700; letter-spacing: -0.04em; color: var(--startup); display: block; margin-bottom: 2px; }
.funding-company { font-size: 14px; font-weight: 600; color: var(--text-primary); margin-bottom: 4px; }
.funding-details { font-size: 11.5px; color: var(--text-muted); line-height: 1.5; }
.funding-stage { display: inline-block; padding: 2px 7px; background: var(--startup-bg); color: var(--startup); border: 1px solid var(--startup-border); border-radius: 4px; font-size: 10px; font-weight: 600; margin-top: 6px; }
.stocks-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 10px; }
.stock-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 14px; box-shadow: var(--shadow-sm); }
.stock-ticker { font-size: 13px; font-weight: 700; color: var(--text-muted); letter-spacing: 0.05em; margin-bottom: 2px; }
.stock-name { font-size: 12px; color: var(--text-muted); margin-bottom: 8px; }
.stock-price { font-size: 20px; font-weight: 700; letter-spacing: -0.03em; color: var(--text-primary); }
.stock-change { font-size: 13px; font-weight: 600; margin: 2px 0 8px; display: flex; align-items: center; gap: 3px; }
.stock-change.positive { color: #16A34A; }
.stock-change.negative { color: #DC2626; }
.stock-reason { font-size: 11.5px; color: var(--text-muted); line-height: 1.4; margin-bottom: 8px; }
.stock-news-link { font-size: 11.5px; color: #2563EB; text-decoration: none; font-weight: 500; }
.market-intro { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px 20px; margin-bottom: 14px; box-shadow: var(--shadow-sm); }
.report-footer { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); padding: 24px 28px; margin-top: 36px; box-shadow: var(--shadow-sm); }
.footer-title { font-size: 14px; font-weight: 700; color: var(--text-primary); margin-bottom: 16px; padding-bottom: 10px; border-bottom: 1px solid var(--border); }
.sources-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; margin-bottom: 20px; }
.sources-section h4 { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: var(--text-muted); margin-bottom: 8px; display: flex; align-items: center; gap: 4px; }
.sources-section ul { list-style: none; display: flex; flex-direction: column; gap: 5px; }
.sources-section a { font-size: 12.5px; color: #2563EB; text-decoration: none; }
.sources-section a:hover { text-decoration: underline; }
.footer-meta { border-top: 1px solid var(--border); padding-top: 14px; display: flex; gap: 16px; flex-wrap: wrap; }
.footer-meta p { font-size: 11.5px; color: var(--text-muted); display: flex; align-items: center; gap: 5px; }
@media (max-width: 900px) {
  .news-card.featured, .news-card.secondary, .news-card.standard { grid-column: span 12; }
  .hero-title { font-size: 30px; }
  .masthead-nav { display: none; }
}
</style>
</head>
<body>

<!-- STICKY NAV -->
<header class="masthead">
  <div class="masthead-inner">
    <div class="masthead-brand">
      <span class="masthead-title">AI Daily</span>
      <span class="masthead-edition">{DATE_SHORT}</span>
    </div>
    <nav class="masthead-nav">
      <a href="#dev-tools"><i data-lucide="monitor"></i> Dev Tools</a>
      <a href="#robotics"><i data-lucide="bot"></i> Robotics</a>
      <a href="#defense"><i data-lucide="shield"></i> Defense</a>
      <a href="#space"><i data-lucide="rocket"></i> Space</a>
      <a href="#startups"><i data-lucide="banknote"></i> Startups</a>
      <a href="#markets"><i data-lucide="bar-chart-2"></i> Markets</a>
      <a href="#sources"><i data-lucide="paperclip"></i> Sources</a>
    </nav>
    <span class="masthead-version">Extended</span>
  </div>
</header>

<!-- HERO -->
<div class="hero-header">
  <div class="hero-inner">
    <div class="hero-date">{DAY_OF_WEEK}, {DATE_LONG} · Morning Edition</div>
    <h1 class="hero-title">AI Daily — <span>Your Morning</span><br>AI Briefing</h1>
    <p class="hero-tagline">Everything you need to know about artificial intelligence from the last 24 hours.</p>
    <div class="hero-stats">
      <div class="hero-stat-item">
        <span class="hero-stat-num">{ARTICLES_REVIEWED}</span>
        <span class="hero-stat-label">articles reviewed</span>
      </div>
      <div class="hero-stat-item">
        <span class="hero-stat-num">{SECTIONS_COUNT}</span>
        <span class="hero-stat-label">topic sections</span>
      </div>
      <div class="hero-stat-item">
        <span class="hero-stat-num">{SOURCES_COUNT}</span>
        <span class="hero-stat-label">verified sources</span>
      </div>
    </div>
  </div>
</div>

<div class="page-wrapper">

  <!-- BREAKING BANNER — include only if there is urgent news, otherwise remove this block -->
  <!-- <div class="breaking-banner" role="alert">
    <span class="breaking-tag"><i data-lucide="zap"></i> BREAKING</span>
    {BREAKING_NEWS_TEXT}
  </div> -->

  <!-- TOPIC SECTIONS — generate only those with last-24h news -->

  <!-- Dev Tools section example: -->
  <section class="news-section" id="dev-tools">
    <div class="section-header">
      <span class="section-icon"><i data-lucide="monitor"></i></span>
      <div class="section-meta">
        <span class="section-overline">Section</span>
        <h2 class="section-title">Developer Tools</h2>
      </div>
      <span class="section-count">{N} articles</span>
    </div>
    <div class="section-divider" style="background: #2563EB;"></div>
    <div class="articles-grid">
      <!-- First (most important) story: class="featured" -->
      <!-- Second: class="secondary" -->
      <!-- Third–fourth: class="standard" -->
      <!-- Full-width article: class="full" -->
    </div>
  </section>

  <!-- Other sections with their colors and icons:
    Robotics:  id="robotics", divider #16A34A, icon: bot
    Defense:   id="defense",  divider #DC2626, icon: shield
    Space:     id="space",    divider #7C3AED, icon: rocket
    Startups:  id="startups", divider #EA580C, icon: banknote
    Markets (conditional): id="markets", divider #0F766E, icon: bar-chart-2
  -->

  <!-- SOURCES FOOTER -->
  <footer class="report-footer" id="sources">
    <h3 class="footer-title"><i data-lucide="paperclip"></i> All report sources</h3>
    <div class="sources-grid">
      <!-- one div.sources-section per content section -->
    </div>
    <div class="footer-meta">
      <p><i data-lucide="cpu"></i> Generated: {DATETIME} by Claude AI News Specialist</p>
      <p><i data-lucide="clock"></i> Time window: last 24 hours</p>
      <p><i data-lucide="bar-chart-2"></i> Sources analyzed: {N}</p>
      <p><i data-lucide="file-text"></i> Edition: Extended</p>
    </div>
  </footer>

</div>
<script>lucide.createIcons();</script>
</body>
</html>
```

### Article Card Structure:

```html
<article class="news-card featured">  <!-- or secondary / standard / full -->
  <div class="card-image-placeholder"><i data-lucide="{SECTION_ICON}"></i></div>
  <div class="card-body">
    <div class="card-tags">
      <span class="badge badge-{SECTION}"><i data-lucide="{ICON}"></i> {SECTION NAME}</span>
      <span class="badge badge-breakthrough"><i data-lucide="sparkles"></i> Breakthrough</span>  <!-- or badge-important / badge-info -->
      <!-- optionally: <span class="badge badge-unverified"><i data-lucide="alert-triangle"></i> UNVERIFIED</span> -->
    </div>
    <h2 class="article-title">{TITLE}</h2>
    <p class="article-deck">{LEAD — 1 sentence}</p>
    <!-- optional stat-row for key numbers -->
    <div class="stat-row">
      <div class="stat-highlight"><span class="stat-number">{NUMBER}</span><span class="stat-label">{DESCRIPTION}</span></div>
    </div>
    <ul class="bullet-list">
      <li>Fact 1 — <strong>key value</strong></li>
      <li>Fact 2</li>
      <li>Fact 3</li>
    </ul>
    <!-- Extended version — add for BREAKTHROUGH or IMPORTANT: -->
    <div class="extended-content">
      <p class="body-text">Context...</p>
      <blockquote class="article-quote"><p>"Quote"</p><cite>— Person, Title</cite></blockquote>
      <p class="body-text implications"><i data-lucide="lightbulb"></i> <strong>Implications:</strong> ...</p>
    </div>
    <div class="card-footer">
      <a href="{URL}" class="source-link" target="_blank" rel="noopener">
        <img src="https://www.google.com/s2/favicons?domain={DOMAIN}&sz=16" alt="">
        {SOURCE NAME}
      </a>
      <span class="pub-time">{PUBLICATION DATE}</span>
    </div>
  </div>
</article>
```

### Layout Rule:
- 1st article in section → `featured` (span 7)
- 2nd article → `secondary` (span 5)
- 3rd–4th articles → `standard` (span 6) × 2
- Full-width article → `full` (span 12)

### Section Icons (Lucide):
- Dev Tools: `monitor` / badge: `badge-dev`
- Robotics: `bot` / badge: `badge-robot`
- Drones: `plane`
- Defense: `shield` / badge: `badge-defense`
- Space: `rocket` / badge: `badge-space`
- AI in Space: `satellite`
- Startups: `banknote` / badge: `badge-startup`
- Markets: `bar-chart-2` / badge: `badge-market`
- BREAKTHROUGH: `sparkles`
- IMPORTANT: `alert-circle`
- UNVERIFIED: `alert-triangle`
- Implications: `lightbulb`
- Stock up: `trending-up`
- Stock down: `trending-down`

### Markets Section — conditional only:
Add ONLY if price change >±5%, earnings report, or major announcement for:
NVDA, META, TSLA, MSFT, GOOGL, AAPL, AMZN, ORCL, AMD, PLTR, VST, CEG, SMR, NEE.

## STEP 5 — Output

Output ONLY the complete HTML document. No explanations, no markdown fences. \
Start directly with <!DOCTYPE html>.
"""


def get_date_info() -> dict:
    warsaw = ZoneInfo("Europe/Warsaw")
    now = datetime.now(warsaw)
    return {
        "date": now.strftime("%Y-%m-%d"),
        "date_long": now.strftime("%B %d, %Y"),
        "day": now.strftime("%A"),
        "month": now.strftime("%B"),
        "year": str(now.year),
        "datetime": now.strftime("%Y-%m-%d %H:%M %Z"),
    }


def run_agent(client: anthropic.Anthropic, dates: dict) -> str:
    model = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")
    user_message = (
        f"Generate today's AI Daily Brief.\n\n"
        f"Date: {dates['date']}\n"
        f"Day: {dates['day']}\n"
        f"Month: {dates['month']}\n"
        f"Year: {dates['year']}\n\n"
        "Run all 8 searches, filter results to the last 24 hours, verify sources, "
        "then output the complete HTML document starting with <!DOCTYPE html>."
    )

    messages: list = [{"role": "user", "content": user_message}]

    for iteration in range(30):
        response = client.messages.create(
            model=model,
            max_tokens=32000,
            system=SYSTEM_PROMPT,
            tools=[{
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 10,
            }],
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            break

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    query = getattr(block, "input", {}).get("query", "")
                    print(f"  searching: {query}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": [],
                    })
            if tool_results:
                messages.append({"role": "user", "content": tool_results})

    for block in response.content:
        if hasattr(block, "text"):
            text = block.text
            idx = text.find("<!DOCTYPE html>")
            if idx == -1:
                idx = text.find("<html")
            if idx >= 0:
                return text[idx:]

    raise RuntimeError("Claude did not return an HTML document in its response.")


def rebuild_index(outputs_dir: Path) -> None:
    reports = sorted(outputs_dir.glob("AI_Daily_*.html"), reverse=True)
    items = "\n".join(
        f'    <li><a href="outputs/{r.name}">'
        f'<span class="date">{r.stem.replace("AI_Daily_", "")}</span>'
        f'<span class="label">AI Daily Brief</span></a></li>'
        for r in reports
    )
    if not items:
        items = '    <li style="color:#6B7280;padding:14px">No reports generated yet.</li>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Daily — Archive</title>
<style>
  body {{ font-family: system-ui, sans-serif; background: #F3F4F6; color: #111827; margin: 0; padding: 40px 16px; }}
  .container {{ max-width: 640px; margin: 0 auto; }}
  h1 {{ font-size: 28px; font-weight: 800; letter-spacing: -.03em; margin-bottom: 8px; }}
  p.sub {{ color: #6B7280; font-size: 14px; margin-bottom: 32px; }}
  ul {{ list-style: none; display: flex; flex-direction: column; gap: 10px; padding: 0; }}
  li a {{ display: flex; align-items: center; gap: 16px; background: #fff; border: 1px solid #E5E7EB; border-radius: 10px; padding: 14px 18px; text-decoration: none; color: inherit; transition: box-shadow .15s; }}
  li a:hover {{ box-shadow: 0 4px 12px rgba(0,0,0,.08); }}
  .date {{ font-size: 13px; font-weight: 700; color: #2563EB; font-variant-numeric: tabular-nums; }}
  .label {{ font-size: 14px; font-weight: 500; color: #374151; }}
</style>
</head>
<body>
<div class="container">
  <h1>AI Daily</h1>
  <p class="sub">Daily AI news briefing — generated automatically every morning.</p>
  <ul>
{items}
  </ul>
</div>
</body>
</html>"""

    Path("index.html").write_text(html, encoding="utf-8")
    print("updated index.html")


def main() -> None:
    client = anthropic.Anthropic()
    dates = get_date_info()
    print(f"generating AI Daily Brief for {dates['date']}...")

    outputs_dir = Path("outputs")
    outputs_dir.mkdir(exist_ok=True)

    output_path = outputs_dir / f"AI_Daily_{dates['date']}.html"
    if output_path.exists():
        print(f"report already exists: {output_path} — skipping generation")
    else:
        html = run_agent(client, dates)
        output_path.write_text(html, encoding="utf-8")
        print(f"saved {output_path}")

    rebuild_index(outputs_dir)


if __name__ == "__main__":
    main()
