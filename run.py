#!/usr/bin/env python3
"""AI Daily Brief — asks an agent for structured content and renders stable HTML."""

import html
import json
import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo  # Python < 3.9


SECTION_CONFIG = {
    "dev-tools": {"title": "Developer Tools", "icon": "monitor", "color": "#2563EB", "badge": "dev", "visual": "DEV"},
    "robotics": {"title": "Robotics", "icon": "bot", "color": "#16A34A", "badge": "robot", "visual": "BOT"},
    "defense": {"title": "Defense", "icon": "shield", "color": "#DC2626", "badge": "defense", "visual": "DEF"},
    "space": {"title": "Space", "icon": "rocket", "color": "#7C3AED", "badge": "space", "visual": "ORB"},
    "startups": {"title": "Startups", "icon": "banknote", "color": "#EA580C", "badge": "startup", "visual": "CAP"},
    "markets": {"title": "Markets", "icon": "bar-chart-2", "color": "#0F766E", "badge": "market", "visual": "MKT"},
}
SECTION_ORDER = tuple(SECTION_CONFIG)
COPILOT_MODEL = os.environ.get("COPILOT_MODEL", "auto").strip()
IMAGE_CACHE: dict[str, str] = {}
DEFAULT_RESEARCHER_PROMPT_PATH = "agents/section-researcher.md"
DEFAULT_EDITOR_PROMPT_PATH = "agents/editor.md"
MIN_SOURCES_PER_SECTION = int(os.environ.get("MIN_SOURCES_PER_SECTION", "3"))
TARGET_SOURCES_PER_SECTION = int(os.environ.get("TARGET_SOURCES_PER_SECTION", "6"))
MIN_ARTICLES_PER_SECTION = int(os.environ.get("MIN_ARTICLES_PER_SECTION", "3"))
RESEARCH_MAX_ATTEMPTS = int(os.environ.get("RESEARCH_MAX_ATTEMPTS", "1"))
AGGREGATOR_DOMAINS = (
    "news.google.",
    "bing.com",
    "news.yahoo.",
    "msn.com",
    "aol.com",
)

SECTION_TITLES = {
    "en": {
        "dev-tools": "Developer Tools",
        "robotics": "Robotics",
        "defense": "Defense",
        "space": "Space",
        "startups": "Startups",
        "markets": "Markets",
    },
    "pl": {
        "dev-tools": "Narzędzia developerskie",
        "robotics": "Robotyka",
        "defense": "Obronność",
        "space": "Kosmos",
        "startups": "Startupy",
        "markets": "Rynki",
    },
}

UI_COPY = {
    "en": {
        "article_singular": "article",
        "article_plural": "articles",
        "articles_reviewed": "articles reviewed",
        "breaking": "BREAKING",
        "edition": "Morning Edition",
        "empty_section": "No articles returned yet. This section should trigger deeper source discovery on the next generation run.",
        "expand": "Read full brief",
        "footer_generated": "Generated",
        "footer_renderer": "by AI Daily structured renderer",
        "footer_sources": "Sources analyzed",
        "footer_window": "Time window: last 24 hours",
        "footer_output": "Output: JSON content rendered to HTML",
        "hero": 'AI Daily — <span>Your Morning</span><br>AI Briefing',
        "implications": "Implications",
        "section": "Section",
        "sources": "All report sources",
        "topic_sections": "topic sections",
        "verified_sources": "verified sources",
        "structured": "Structured",
    },
    "pl": {
        "article_singular": "artykuł",
        "article_plural": "artykuły",
        "articles_reviewed": "sprawdzonych artykułów",
        "breaking": "PILNE",
        "edition": "Wydanie poranne",
        "empty_section": "Brak artykułów w tej sekcji. To powinno uruchomić głębszy research przy kolejnej generacji.",
        "expand": "Czytaj pełny brief",
        "footer_generated": "Wygenerowano",
        "footer_renderer": "przez renderer strukturalny AI Daily",
        "footer_sources": "Przeanalizowane źródła",
        "footer_window": "Okno czasowe: ostatnie 24 godziny",
        "footer_output": "Output: treść JSON wyrenderowana do HTML",
        "hero": 'AI Daily — <span>Twój poranny</span><br>brief AI',
        "implications": "Znaczenie",
        "section": "Sekcja",
        "sources": "Wszystkie źródła raportu",
        "topic_sections": "sekcji tematycznych",
        "verified_sources": "zweryfikowanych źródeł",
        "structured": "Strukturalny",
    },
}

SYSTEM_PROMPT = """\
You are an AI News Specialist. Generate only structured content for a daily news briefing.
Do not generate HTML, CSS, Markdown, code fences, or explanations.

Use the repository owner's custom brief from agents/coverage.md. If it conflicts with default topics,
the custom brief wins.

Process:
1. Run the searches requested by agents/coverage.md, replacing {DATE}, {YEAR}, and {MONTH}.
2. Keep only news published in the last 24 hours.
3. Use only these section ids, in this exact order: dev-tools, robotics, defense, space, startups, markets.
4. Target 3-4 important stories per section.
5. If a section has fewer than 3 strong stories, broaden source discovery and continue searching the source map.
6. Never fabricate filler: if a section still has fewer than 3 strong stories, include only credible stories and mark uncertain ones with verified=false.
7. Return every canonical section id even when a section has fewer than 3 articles.
8. Verify dates and sources. Set verified=false if uncertain.
9. Return JSON only.

JSON shape:
{
  "title": "AI Daily",
  "tagline": "Everything you need to know about artificial intelligence from the last 24 hours.",
  "articles_reviewed": 24,
  "breaking": "optional urgent one-sentence item or empty string",
  "sections": [
    {
      "id": "dev-tools",
      "title": "Developer Tools",
      "icon": "monitor",
      "color": "#2563EB",
      "articles": [
        {
          "title": "Short factual headline",
          "subtitle": "One-sentence summary shown in collapsed view.",
          "importance": "breakthrough|important|info",
          "verified": true,
          "stats": [{"number": "2x", "label": "short label"}],
          "facts": ["Fact 1", "Fact 2", "Fact 3"],
          "body": ["Context paragraph 1", "Context paragraph 2"],
          "quote": {"text": "Optional quote", "cite": "Optional source"},
          "implications": "Why this matters.",
          "source_name": "Source",
          "source_url": "https://example.com/article",
          "image_url": "https://example.com/optional-article-preview.jpg",
          "published_at": "2026-05-16"
        }
      ]
    }
  ]
}

Allowed default section ids: dev-tools, robotics, defense, space, startups, markets.
If you can identify a source-provided article preview image, include it as image_url. Use only http/https URLs from the source page metadata or official source assets.
For custom topics, use lowercase kebab-case ids and include title, icon, and color.
"""

REPORT_CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }
body { font-family: 'Inter', system-ui, sans-serif; font-size: 15px; line-height: 1.65; color: #111827; background: #F3F4F6; -webkit-font-smoothing: antialiased; }
:root {
  --bg-page: #F3F4F6; --bg-card: #FFFFFF; --text-primary: #111827; --text-secondary: #374151; --text-muted: #6B7280;
  --border: #E5E7EB; --border-strong: #D1D5DB;
  --shadow-sm: 0 1px 3px rgba(0,0,0,.08); --shadow-md: 0 4px 12px rgba(0,0,0,.08);
  --radius: 12px; --radius-sm: 8px; --radius-pill: 9999px;
  --dev: #2563EB; --dev-bg: #EFF6FF; --dev-border: #BFDBFE;
  --ai-tool: #DB2777; --ai-tool-bg: #FDF2F8; --ai-tool-border: #FBCFE8;
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
.masthead-github { flex-shrink: 0; display: flex; align-items: center; justify-content: center; width: 32px; height: 32px; border-radius: 50%; color: var(--text-muted); transition: background 0.15s, color 0.15s; text-decoration: none; }
.masthead-github:hover { background: var(--bg-page); color: #111827; }
.masthead-github svg { width: 18px; height: 18px; }
.language-toggle { flex-shrink: 0; display: inline-flex; gap: 3px; padding: 3px; background: #F3F4F6; border: 1px solid var(--border); border-radius: var(--radius-pill); }
.language-toggle button { border: 0; background: transparent; color: var(--text-muted); border-radius: var(--radius-pill); padding: 4px 9px; font: inherit; font-size: 11px; font-weight: 700; cursor: pointer; }
.language-toggle button.active { background: #111827; color: #fff; }
.language-panel { display: none; }
.language-panel.active { display: block; }
.hero-header { background: linear-gradient(135deg, #111827 0%, #1e3a5f 100%); color: white; padding: 48px 16px 40px; margin-bottom: 28px; }
.hero-inner { max-width: 1180px; margin: 0 auto; }
.hero-date { font-size: 12px; font-weight: 500; color: #93C5FD; text-transform: uppercase; letter-spacing: 0.12em; margin-bottom: 10px; }
.hero-title { font-size: 42px; font-weight: 800; letter-spacing: -0.04em; line-height: 1.05; margin-bottom: 12px; }
.hero-title span { color: #60A5FA; }
.hero-tagline { font-size: 15px; color: #9CA3AF; max-width: 520px; line-height: 1.6; margin-bottom: 24px; }
.hero-stats { display: flex; gap: 32px; flex-wrap: wrap; }
.hero-stat-num { font-size: 28px; font-weight: 700; color: #fff; letter-spacing: -0.03em; display: block; }
.hero-stat-label { font-size: 11px; color: #9CA3AF; font-weight: 500; text-transform: uppercase; letter-spacing: 0.08em; }
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
.empty-section { grid-column: span 12; background: #fff; border: 1px dashed var(--border-strong); border-radius: var(--radius); padding: 18px; color: var(--text-muted); font-size: 13px; }
.news-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); display: flex; flex-direction: column; overflow: hidden; transition: box-shadow 0.15s, transform 0.15s; box-shadow: var(--shadow-sm); }
.news-card:hover { box-shadow: var(--shadow-md); transform: translateY(-1px); }
.news-card.featured { grid-column: span 7; }
.news-card.secondary { grid-column: span 5; }
.news-card.standard { grid-column: span 6; }
.news-card.full { grid-column: span 12; }
.news-card > summary { list-style: none; cursor: pointer; }
.news-card > summary::-webkit-details-marker { display: none; }
.card-summary { display: block; }
.card-summary-content { padding: 16px 18px; }
.expand-hint { display: inline-flex; align-items: center; gap: 5px; font-size: 12px; font-weight: 600; color: #2563EB; }
.expand-hint [data-lucide] { width: 13px; height: 13px; transition: transform .15s; }
.news-card[open] .expand-hint [data-lucide] { transform: rotate(180deg); }
.card-details { border-top: 1px solid var(--border); padding: 14px 18px 16px; display: flex; flex-direction: column; flex: 1; }
.card-image-placeholder { width: 100%; aspect-ratio: 16/7; background: #F3F4F6; background: linear-gradient(135deg, color-mix(in srgb, var(--accent) 14%, #FFFFFF), #F3F4F6); display: flex; align-items: center; justify-content: center; position: relative; overflow: hidden; }
.card-image-placeholder::before { content: ''; position: absolute; inset: 16px; border: 1px solid color-mix(in srgb, var(--accent) 24%, transparent); border-radius: 18px; }
.card-image { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; z-index: 1; }
.card-image-placeholder.has-image::after { content: ''; position: absolute; inset: 0; z-index: 2; background: linear-gradient(180deg, rgba(17,24,39,0) 45%, rgba(17,24,39,.22)); pointer-events: none; }
.card-visual-svg { width: 100%; height: 100%; display: block; color: var(--accent); position: relative; z-index: 0; }
.card-visual-label { font: 800 22px/1 Inter, system-ui, sans-serif; letter-spacing: .12em; fill: currentColor; }
.card-summary .card-image-placeholder { border-bottom: 1px solid var(--border); }
.card-tags { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin-bottom: 10px; }
.badge { display: inline-flex; align-items: center; gap: 4px; padding: 3px 9px; border-radius: var(--radius-pill); font-size: 10.5px; font-weight: 600; letter-spacing: 0.04em; text-transform: uppercase; line-height: 1; white-space: nowrap; }
.badge-dev { background: var(--dev-bg); color: var(--dev); border: 1px solid var(--dev-border); }
.badge-ai-tool { background: var(--ai-tool-bg); color: var(--ai-tool); border: 1px solid var(--ai-tool-border); }
.badge-robot { background: var(--robot-bg); color: var(--robot); border: 1px solid var(--robot-border); }
.badge-defense { background: var(--defense-bg); color: var(--defense); border: 1px solid var(--defense-border); }
.badge-space { background: var(--space-bg); color: var(--space); border: 1px solid var(--space-border); }
.badge-startup { background: var(--startup-bg); color: var(--startup); border: 1px solid var(--startup-border); }
.badge-market { background: var(--market-bg); color: var(--market); border: 1px solid var(--market-border); }
.badge-custom { background: #F9FAFB; color: #374151; border: 1px solid #E5E7EB; }
.badge-breakthrough { background: #F5F3FF; color: #7C3AED; border: 1px solid #DDD6FE; }
.badge-important { background: #FFFBEB; color: #D97706; border: 1px solid #FDE68A; }
.badge-info { background: #F9FAFB; color: #6B7280; border: 1px solid #E5E7EB; }
.badge-unverified { background: #FFF7ED; color: #C2410C; border: 1px solid #FED7AA; }
.article-title { font-size: 17px; font-weight: 700; line-height: 1.3; color: var(--text-primary); margin-bottom: 8px; letter-spacing: -0.02em; }
.news-card.featured .article-title { font-size: 21px; }
.article-deck { font-size: 13.5px; color: var(--text-secondary); line-height: 1.55; margin-bottom: 10px; font-style: italic; }
.bullet-list { list-style: none; margin-bottom: 14px; display: flex; flex-direction: column; gap: 6px; }
.bullet-list li { font-size: 13.5px; color: var(--text-secondary); line-height: 1.55; padding-left: 14px; position: relative; }
.bullet-list li::before { content: '•'; position: absolute; left: 0; color: var(--text-muted); font-weight: 700; }
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
"""


def e(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def get_date_info() -> dict:
    warsaw = ZoneInfo("Europe/Warsaw")
    now = datetime.now(warsaw)
    months_pl = {
        1: "stycznia",
        2: "lutego",
        3: "marca",
        4: "kwietnia",
        5: "maja",
        6: "czerwca",
        7: "lipca",
        8: "sierpnia",
        9: "września",
        10: "października",
        11: "listopada",
        12: "grudnia",
    }
    days_pl = {
        0: "Poniedziałek",
        1: "Wtorek",
        2: "Środa",
        3: "Czwartek",
        4: "Piątek",
        5: "Sobota",
        6: "Niedziela",
    }
    return {
        "date": now.strftime("%Y-%m-%d"),
        "date_long": now.strftime("%B %d, %Y"),
        "date_long_pl": f"{now.day} {months_pl[now.month]} {now.year}",
        "date_short": now.strftime("%b %d"),
        "date_short_pl": f"{now.day:02d}.{now.month:02d}",
        "day": now.strftime("%A"),
        "day_pl": days_pl[now.weekday()],
        "month": now.strftime("%B"),
        "year": str(now.year),
        "datetime": now.strftime("%Y-%m-%d %H:%M %Z"),
    }


def load_prompt_file(path: str | Path) -> str:
    prompt_path = Path(path)
    if not prompt_path.exists():
        raise FileNotFoundError(f"Agent prompt file not found: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8").strip()


def load_agent_prompt() -> str:
    return load_prompt_file(os.environ.get("AGENT_PROMPT_PATH", "agents/coverage.md"))


def load_researcher_prompt() -> str:
    return load_prompt_file(os.environ.get("RESEARCHER_PROMPT_PATH", DEFAULT_RESEARCHER_PROMPT_PATH))


def load_editor_prompt() -> str:
    return load_prompt_file(os.environ.get("EDITOR_PROMPT_PATH", DEFAULT_EDITOR_PROMPT_PATH))


def load_translation_prompt() -> str:
    prompt_path = Path(os.environ.get("TRANSLATION_PROMPT_PATH", "agents/translate-agent.md"))
    if not prompt_path.exists():
        raise FileNotFoundError(f"Translation prompt file not found: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8").strip()


def build_system_prompt() -> str:
    return f"{SYSTEM_PROMPT}\n\n## CUSTOM AGENT BRIEF FROM agents/coverage.md\n\n{load_agent_prompt()}"


def build_user_message(dates: dict) -> str:
    return (
        f"Generate today's structured AI Daily Brief content.\n\n"
        f"Date: {dates['date']}\n"
        f"Day: {dates['day']}\n"
        f"Month: {dates['month']}\n"
        f"Year: {dates['year']}\n\n"
        "Return JSON only. The app will render HTML."
    )


def extract_json(text: str, require_sections: bool = False) -> dict:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.startswith("json"):
            stripped = stripped[4:].strip()

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start < 0 or end < start:
        raise RuntimeError("The agent did not return a JSON object.")

    data = json.loads(stripped[start : end + 1])
    if require_sections and not isinstance(data.get("sections"), list):
        raise RuntimeError("Agent JSON must contain a 'sections' array.")
    return data


def is_aggregator_url(url: str) -> bool:
    netloc = urlparse(url).netloc.lower()
    return any(domain in netloc for domain in AGGREGATOR_DOMAINS)


def research_output_path(dates: dict, section_id: str) -> Path:
    return Path(".copilot-output") / "research" / dates["date"] / f"{section_id}.research.json"


def validate_research_pack(pack: dict, expected_section: str) -> list[str]:
    errors: list[str] = []
    if pack.get("schema_version") != "research-pack.v1":
        errors.append(f"{expected_section}: schema_version must be research-pack.v1")
    if pack.get("section") != expected_section:
        errors.append(f"{expected_section}: section mismatch")

    source_ids = set()
    canonical_urls = set()
    evidence_ids = set()
    image_ids = set()
    for source in pack.get("sources") or []:
        source_id = source.get("source_id")
        canonical_url = source.get("canonical_url") or ""
        if source_id:
            source_ids.add(source_id)
        if not is_http_url(canonical_url):
            errors.append(f"{expected_section}: source {source_id} missing canonical_url")
        elif is_aggregator_url(canonical_url):
            errors.append(f"{expected_section}: source {source_id} uses aggregator canonical_url {canonical_url}")
        else:
            canonical_urls.add(canonical_url)
        if source.get("is_aggregator") is True:
            errors.append(f"{expected_section}: source {source_id} is marked as aggregator")
        for image in source.get("image_candidates") or []:
            image_id = image.get("image_id")
            if image_id:
                image_ids.add(image_id)
            if image.get("verified") is True and not is_http_url(str(image.get("url") or "")):
                errors.append(f"{expected_section}: image {image_id} is verified without an HTTP URL")

    for evidence in pack.get("evidence") or []:
        evidence_id = evidence.get("evidence_id")
        if evidence_id:
            evidence_ids.add(evidence_id)
        if evidence.get("source_id") not in source_ids:
            errors.append(f"{expected_section}: evidence {evidence_id} references missing source")
        if not evidence.get("quote"):
            errors.append(f"{expected_section}: evidence {evidence_id} has no quote/paraphrase")

    for claim in pack.get("claims") or []:
        claim_id = claim.get("claim_id")
        claim_source_ids = claim.get("source_ids") or []
        claim_evidence_ids = claim.get("evidence_ids") or []
        missing_sources = [source_id for source_id in claim_source_ids if source_id not in source_ids]
        missing_evidence = [evidence_id for evidence_id in claim_evidence_ids if evidence_id not in evidence_ids]
        if not claim_source_ids or not claim_evidence_ids:
            errors.append(f"{expected_section}: claim {claim_id} has no source/evidence mapping")
        if missing_sources:
            errors.append(f"{expected_section}: claim {claim_id} references missing sources {missing_sources}")
        if missing_evidence:
            errors.append(f"{expected_section}: claim {claim_id} references missing evidence {missing_evidence}")

    for story in pack.get("story_candidates") or []:
        for image_id in story.get("image_candidate_ids") or []:
            if image_id not in image_ids:
                errors.append(f"{expected_section}: story {story.get('story_id')} references missing image {image_id}")

    return errors


def research_indexes(research_packs: list[dict]) -> tuple[set[str], set[str], dict[str, str], set[str]]:
    source_ids: set[str] = set()
    evidence_ids: set[str] = set()
    verified_images: dict[str, str] = {}
    verified_image_urls: set[str] = set()
    for pack in research_packs:
        for source in pack.get("sources") or []:
            if source.get("source_id"):
                source_ids.add(source["source_id"])
            for image in source.get("image_candidates") or []:
                if image.get("verified") is True and is_http_url(str(image.get("url") or "")):
                    verified_images[image.get("image_id")] = image["url"]
                    verified_image_urls.add(image["url"])
        for evidence in pack.get("evidence") or []:
            if evidence.get("evidence_id"):
                evidence_ids.add(evidence["evidence_id"])
    return source_ids, evidence_ids, verified_images, verified_image_urls


def strip_unverified_article_images(report: dict, research_packs: list[dict]) -> dict:
    _source_ids, _evidence_ids, verified_images, _verified_image_urls = research_indexes(research_packs)
    for section in report.get("sections") or []:
        for article in section.get("articles") or []:
            image_id = article.get("image_candidate_id")
            image_url = article.get("image_url")
            if not image_id or image_id not in verified_images or image_url != verified_images[image_id]:
                article.pop("image_candidate_id", None)
                article.pop("image_url", None)
    return report


def validate_final_report(report: dict, research_packs: list[dict]) -> list[str]:
    errors: list[str] = []
    source_ids, evidence_ids, verified_images, _verified_image_urls = research_indexes(research_packs)
    sections = {section.get("id"): section for section in report.get("sections") or []}
    for source in report.get("source_index") or []:
        source_url = source.get("canonical_url") or source.get("url") or ""
        if is_aggregator_url(str(source_url)):
            errors.append(f"source_index contains aggregator URL {source_url}")
        if source.get("source_id") and source["source_id"] not in source_ids:
            errors.append(f"source_index references missing source_id {source['source_id']}")
    for section_id in SECTION_ORDER:
        if section_id not in sections:
            errors.append(f"final report missing section {section_id}")

    for section in report.get("sections") or []:
        section_id = section.get("id") or "unknown"
        articles = section.get("articles") or []
        for article in articles:
            title = article.get("title") or "untitled"
            if is_aggregator_url(str(article.get("source_url") or "")):
                errors.append(f"{title}: source_url is an aggregator URL")
            source_items = article.get("sources") if isinstance(article.get("sources"), list) else []
            for source in source_items:
                source_url = source.get("url") or source.get("canonical_url") or ""
                if is_aggregator_url(str(source_url)):
                    errors.append(f"{title}: sources[] contains aggregator URL {source_url}")
            article_source_ids = article.get("source_ids") or []
            article_evidence_ids = article.get("evidence_ids") or []
            if not article_source_ids or not article_evidence_ids:
                errors.append(f"{title}: article missing source_ids/evidence_ids")
            for source_id in article_source_ids:
                if source_id not in source_ids:
                    errors.append(f"{title}: missing source_id {source_id}")
            for evidence_id in article_evidence_ids:
                if evidence_id not in evidence_ids:
                    errors.append(f"{title}: missing evidence_id {evidence_id}")

            claims = article.get("claims") or []
            if not claims:
                errors.append(f"{title}: article has no mapped claims")
            for claim in claims:
                claim_source_ids = claim.get("source_ids") or []
                claim_evidence_ids = claim.get("evidence_ids") or []
                if not claim_source_ids or not claim_evidence_ids:
                    errors.append(f"{title}: claim has no source/evidence mapping")
                for source_id in claim_source_ids:
                    if source_id not in source_ids:
                        errors.append(f"{title}: claim references missing source {source_id}")
                for evidence_id in claim_evidence_ids:
                    if evidence_id not in evidence_ids:
                        errors.append(f"{title}: claim references missing evidence {evidence_id}")

            image_id = article.get("image_candidate_id")
            image_url = article.get("image_url")
            if image_id and image_id not in verified_images:
                errors.append(f"{title}: image_candidate_id is not a verified research image")
            elif image_id and image_url != verified_images[image_id]:
                errors.append(f"{title}: image_url does not match verified image_candidate_id")
    return errors


def invoke_copilot(prompt: str, output_path: Path, allow_urls: bool) -> subprocess.CompletedProcess:
    allow_tool = f"write({output_path})"
    if allow_urls:
        allow_tool = f"url,{allow_tool}"

    command = [
        "copilot",
        "-p",
        prompt,
        "-s",
        f"--allow-tool={allow_tool}",
        "--deny-tool=shell",
        "--no-ask-user",
    ]
    if COPILOT_MODEL:
        command.extend(["--model", COPILOT_MODEL])
    if allow_urls:
        command.append("--allow-all-urls")

    print(f"copilot start: output={output_path} urls={'yes' if allow_urls else 'no'}", flush=True)
    result = subprocess.run(
        command,
        text=True,
        capture_output=True,
        timeout=int(os.environ.get("AGENT_TIMEOUT_SECONDS", "1800")),
        check=False,
    )
    if result.stdout:
        print(result.stdout, end="", flush=True)
    if result.stderr:
        print(result.stderr, end="", flush=True)
    print(f"copilot done: output={output_path} exit={result.returncode}", flush=True)
    return result


def discovery_output_path(dates: dict, section_id: str) -> Path:
    return Path(".copilot-output") / "sources" / dates["date"] / f"{section_id}.sources.json"


def evidence_output_path(dates: dict, section_id: str) -> Path:
    return Path(".copilot-output") / "evidence" / dates["date"] / f"{section_id}.evidence.json"


def validate_discovery_pack(pack: dict, section_id: str) -> list[str]:
    errors: list[str] = []
    if pack.get("schema_version") != "discovery-pack.v1":
        errors.append("schema_version must be discovery-pack.v1")
    if pack.get("section") != section_id:
        errors.append(f"section must be {section_id}")

    sources = pack.get("sources") or []
    if len(sources) < MIN_SOURCES_PER_SECTION:
        errors.append(f"{section_id}: expected at least {MIN_SOURCES_PER_SECTION} qualified sources, got {len(sources)}")
    source_ids: set[str] = set()
    for source in sources:
        source_id = source.get("source_id")
        url = source.get("canonical_url") or source.get("url")
        if not source_id:
            errors.append(f"{section_id}: source missing source_id")
        elif source_id in source_ids:
            errors.append(f"{section_id}: duplicate source_id {source_id}")
        else:
            source_ids.add(source_id)
        if not url:
            errors.append(f"{section_id}: source {source_id or '?'} missing canonical_url")
        elif is_aggregator_url(str(url)):
            errors.append(f"{section_id}: source {source_id or '?'} uses aggregator URL {url}")

    candidates = pack.get("story_candidates") or []
    if len(candidates) < MIN_ARTICLES_PER_SECTION:
        errors.append(f"{section_id}: expected at least {MIN_ARTICLES_PER_SECTION} story candidates, got {len(candidates)}")
    for candidate in candidates:
        for source_id in candidate.get("source_ids") or []:
            if source_id not in source_ids:
                errors.append(f"{section_id}: story candidate references missing source {source_id}")
    return errors


def run_source_discovery(section_id: str, dates: dict) -> dict:
    output_path = discovery_output_path(dates, section_id)
    prompt = (
        "/research\n"
        f"{load_discovery_prompt()}\n\n"
        f"## CUSTOM COVERAGE BRIEF FROM agent.md\n\n{load_agent_prompt()}\n\n"
        "## RUN INPUT\n"
        f"run_date: {dates['date']}\n"
        f"section: {section_id}\n"
        f"section_title: {SECTION_CONFIG[section_id]['title']}\n"
        f"research_window: last 24 hours ending {dates['date']} Europe/Warsaw\n"
        f"minimum_qualified_sources: {MIN_SOURCES_PER_SECTION}\n"
        f"target_qualified_sources: {TARGET_SOURCES_PER_SECTION}\n"
        f"minimum_story_candidates: {MIN_ARTICLES_PER_SECTION}\n"
        f"output_path: {output_path}\n\n"
        f"Write discovery-pack.v1 JSON to {output_path}. Do not edit any other files."
    )
    pack = run_copilot_json(prompt, output_path, allow_urls=True)
    errors = validate_discovery_pack(pack, section_id)
    if errors:
        raise RuntimeError("Discovery pack failed validation:\n" + "\n".join(errors))
    return pack


def run_source_discovery_fleet(dates: dict) -> list[dict]:
    max_workers = int(os.environ.get("DISCOVERY_MAX_WORKERS", os.environ.get("FLEET_MAX_WORKERS", "3")))
    packs_by_section: dict[str, dict] = {}
    errors: list[str] = []
    print(f"running source discovery fleet: workers={max_workers}", flush=True)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(run_source_discovery, section_id, dates): section_id for section_id in SECTION_ORDER}
        for future in as_completed(futures):
            section_id = futures[future]
            try:
                packs_by_section[section_id] = future.result()
                print(f"source discovery complete: {section_id}", flush=True)
            except Exception as error:
                errors.append(f"{section_id}: {error}")
                print(f"source discovery failed: {section_id}: {error}", flush=True)
    if errors:
        raise RuntimeError("Source discovery fleet failed:\n" + "\n".join(errors))
    return [packs_by_section[section_id] for section_id in SECTION_ORDER]


def run_evidence_research(discovery_pack: dict, dates: dict) -> dict:
    section_id = discovery_pack["section"]
    output_path = evidence_output_path(dates, section_id)
    prompt = (
        "/research\n"
        f"{load_evidence_prompt()}\n\n"
        "## RUN INPUT\n"
        f"run_date: {dates['date']}\n"
        f"section: {section_id}\n"
        f"section_title: {SECTION_CONFIG[section_id]['title']}\n"
        f"output_path: {output_path}\n\n"
        "## DISCOVERY PACK\n"
        f"{json.dumps(discovery_pack, ensure_ascii=False)}\n\n"
        f"Write research-pack.v1 JSON to {output_path}. Do not edit any other files."
    )
    pack = run_copilot_json(prompt, output_path, allow_urls=True)
    errors = validate_research_pack(pack, section_id)
    if errors:
        repair_prompt = (
            f"{load_evidence_prompt()}\n\n"
            "## VALIDATION ERRORS TO FIX\n"
            + "\n".join(f"- {error}" for error in errors)
            + "\n\nUse only the discovery pack and the draft evidence pack below. "
            "If a primary source was blocked, use a backup source from the same discovery ledger. "
            f"Write corrected research-pack.v1 JSON to {output_path}. Do not edit any other files.\n\n"
            "## DISCOVERY PACK\n"
            f"{json.dumps(discovery_pack, ensure_ascii=False)}\n\n"
            "## DRAFT EVIDENCE PACK\n"
            f"{json.dumps(pack, ensure_ascii=False)}"
        )
        pack = run_copilot_json(repair_prompt, output_path, allow_urls=False)
        errors = validate_research_pack(pack, section_id)
    if errors:
        raise RuntimeError("Evidence pack failed validation:\n" + "\n".join(errors))
    return pack


def run_evidence_research_fleet(discovery_packs: list[dict], dates: dict) -> list[dict]:
    max_workers = int(os.environ.get("EVIDENCE_MAX_WORKERS", "2"))
    packs_by_section: dict[str, dict] = {}
    errors: list[str] = []
    print(f"running evidence research fleet: workers={max_workers}", flush=True)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(run_evidence_research, pack, dates): pack["section"] for pack in discovery_packs}
        for future in as_completed(futures):
            section_id = futures[future]
            try:
                packs_by_section[section_id] = future.result()
                print(f"evidence research complete: {section_id}", flush=True)
            except Exception as error:
                errors.append(f"{section_id}: {error}")
                print(f"evidence research failed: {section_id}: {error}", flush=True)
    if errors:
        raise RuntimeError("Evidence research fleet failed:\n" + "\n".join(errors))
    return [packs_by_section[section_id] for section_id in SECTION_ORDER]


def run_copilot_json(prompt: str, output_path: Path, allow_urls: bool, require_sections: bool = False) -> dict:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()

    result = invoke_copilot(prompt, output_path, allow_urls)
    if result.returncode != 0:
        raise RuntimeError(f"Copilot CLI failed with exit code {result.returncode}:\n{result.stderr}\n{result.stdout}")
    if not output_path.exists():
        raise RuntimeError(f"Copilot CLI did not create expected JSON file: {output_path}\n{result.stdout}")
    raw_json = output_path.read_text(encoding="utf-8")
    try:
        return extract_json(raw_json, require_sections=require_sections)
    except (json.JSONDecodeError, RuntimeError) as error:
        print(f"warning: agent wrote invalid JSON to {output_path}: {error}; running JSON repair agent", flush=True)
        return repair_agent_json(raw_json, output_path, require_sections=require_sections)


def empty_research_pack(section_id: str, dates: dict, reason: str) -> dict:
    return {
        "schema_version": "research-pack.v1",
        "run_date": dates["date"],
        "section": section_id,
        "section_display_name": SECTION_CONFIG[section_id]["title"],
        "generated_at": datetime.now(ZoneInfo("UTC")).isoformat(),
        "research_window": {"from": dates["date"], "to": dates["date"], "timezone": "Europe/Warsaw"},
        "status": "no-qualified-stories",
        "topic_clusters": [
            {
                "cluster_id": f"cluster_{section_id.replace('-', '_')}_none",
                "label": "No qualified recent stories",
                "queries": [],
            }
        ],
        "sources": [],
        "evidence": [],
        "claims": [],
        "story_candidates": [],
        "rejects": [{"reason": reason[:500]}],
    }


def repair_agent_json(raw_json: str, output_path: Path, require_sections: bool = False) -> dict:
    repair_path = output_path.with_suffix(".repaired.json")
    prompt = (
        "You are a JSON repair agent. Fix the malformed JSON below without adding new facts. "
        "Preserve all object keys and source/evidence mappings. Return JSON only. "
        f"Write the corrected JSON object to {repair_path}. Do not edit any other files.\n\n"
        "## MALFORMED JSON\n"
        f"{raw_json[-60_000:]}"
    )
    result = invoke_copilot(prompt, repair_path, allow_urls=False)
    if result.returncode != 0:
        raise RuntimeError(f"JSON repair agent failed with exit code {result.returncode}:\n{result.stderr}\n{result.stdout}")
    if not repair_path.exists():
        raise RuntimeError(f"JSON repair agent did not create expected file: {repair_path}")
    repaired = repair_path.read_text(encoding="utf-8")
    output_path.write_text(repaired, encoding="utf-8")
    return extract_json(repaired, require_sections=require_sections)


def run_section_research_once(section_id: str, dates: dict, validation_errors: list[str] | None = None) -> dict:
    output_path = research_output_path(dates, section_id)
    retry_note = ""
    if validation_errors:
        retry_note = (
            "\n## PREVIOUS OUTPUT FAILED VALIDATION\n"
            + "\n".join(f"- {error}" for error in validation_errors)
            + "\nFix schema/source/evidence issues only. If fewer than 3 qualified stories exist, keep the sparse pack instead of inventing filler.\n"
        )
    prompt = (
        "/research\n"
        f"{load_researcher_prompt()}\n\n"
        f"## CUSTOM COVERAGE BRIEF FROM agents/coverage.md\n\n{load_agent_prompt()}\n\n"
        "## RUN INPUT\n"
        f"run_date: {dates['date']}\n"
        f"section: {section_id}\n"
        f"section_title: {SECTION_CONFIG[section_id]['title']}\n"
        f"research_window: last 24 hours ending {dates['date']} Europe/Warsaw\n"
        f"preferred_qualified_sources: {MIN_SOURCES_PER_SECTION}\n"
        f"target_qualified_sources: {TARGET_SOURCES_PER_SECTION}\n"
        f"preferred_story_candidates: {MIN_ARTICLES_PER_SECTION}\n"
        f"output_path: {output_path}\n\n"
        f"{retry_note}\n"
        f"Write the research-pack.v1 JSON object to {output_path}. "
        "Do not edit any other files. Do not write Markdown. Do not ask follow-up questions."
    )
    return run_copilot_json(prompt, output_path, allow_urls=True)


def run_section_research(section_id: str, dates: dict) -> dict:
    errors: list[str] | None = None
    pack: dict | None = None
    for attempt in range(1, RESEARCH_MAX_ATTEMPTS + 1):
        print(f"research attempt {attempt}/{RESEARCH_MAX_ATTEMPTS}: {section_id}")
        try:
            pack = run_section_research_once(section_id, dates, errors)
        except RuntimeError as error:
            if "did not create expected JSON file" in str(error):
                print(f"research sparse: {section_id}: agent found no qualified stories and wrote no pack")
                return empty_research_pack(section_id, dates, str(error))
            raise
        errors = validate_research_pack(pack, section_id)
        if not errors:
            return pack
        print(f"research validation failed: {section_id}: {'; '.join(errors)}")
    assert pack is not None
    raise RuntimeError("Research pack failed validation after retries:\n" + "\n".join(errors or []))


def run_section_research_fleet(dates: dict) -> list[dict]:
    max_workers = int(os.environ.get("FLEET_MAX_WORKERS", "3"))
    packs_by_section: dict[str, dict] = {}
    errors: list[str] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(run_section_research, section_id, dates): section_id for section_id in SECTION_ORDER}
        for future in as_completed(futures):
            section_id = futures[future]
            try:
                packs_by_section[section_id] = future.result()
                print(f"research complete: {section_id}")
            except Exception as error:
                errors.append(f"{section_id}: {error}")
                print(f"research failed: {section_id}: {error}")
    if errors:
        raise RuntimeError("Section research fleet failed:\n" + "\n".join(errors))
    return [packs_by_section[section_id] for section_id in SECTION_ORDER]


def run_editor_report(research_packs: list[dict], dates: dict, validation_errors: list[str] | None = None) -> dict:
    output_path = Path(os.environ.get("COPILOT_OUTPUT_PATH", ".copilot-output/report.json"))
    retry_note = ""
    if validation_errors:
        retry_note = (
            "\n## VALIDATION ERRORS TO FIX\n"
            + "\n".join(f"- {error}" for error in validation_errors)
            + "\nReturn corrected JSON only. Do not add facts not present in the research packs.\n"
        )
    prompt = (
        f"{load_editor_prompt()}\n\n"
        f"Date: {dates['date']}\n"
        f"Canonical section order: {', '.join(SECTION_ORDER)}\n"
        f"Preferred final articles per section: {MIN_ARTICLES_PER_SECTION}; sparse or empty sections are allowed when research packs lack qualified candidates.\n"
        f"Write the final renderer-compatible final-report.v1 JSON to {output_path}.\n"
        "Do not use web search. Do not edit any other files. Do not write Markdown.\n"
        f"{retry_note}\n"
        "## RESEARCH PACKS\n"
        f"{json.dumps(research_packs, ensure_ascii=False)}"
    )
    return run_copilot_json(prompt, output_path, allow_urls=False, require_sections=True)


def recover_report_json(research_notes: str, output_path: Path, dates: dict) -> dict:
    notes = research_notes[-55_000:]
    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        "You are the synthesis pass for AI Daily. The research pass produced notes but failed to write JSON.\n"
        f"Date: {dates['date']}\n\n"
        "Convert the research notes below into the required final JSON object.\n"
        "Use only facts present in the notes. Do not use web search. Do not add Markdown or explanations.\n"
        "Return every canonical section id: dev-tools, robotics, defense, space, startups, markets. Prefer 3-4 articles per section, but do not drop a section solely because it has fewer candidates.\n"
        f"Write the final JSON object to {output_path} and do not edit any other files.\n\n"
        f"## RESEARCH NOTES\n\n{notes}"
    )
    return run_copilot_json(prompt, output_path, allow_urls=False, require_sections=True)


def run_copilot_agent(dates: dict, system_prompt: str) -> dict:
    output_path = Path(os.environ.get("COPILOT_OUTPUT_PATH", ".copilot-output/report.json"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()

    prompt = (
        "/research\n"
        f"{system_prompt}\n\n"
        f"{build_user_message(dates)}\n\n"
        f"Write the final JSON object to {output_path}. "
        "Do not edit any other files. Do not write Markdown. Do not ask follow-up questions."
    )
    result = invoke_copilot(prompt, output_path, allow_urls=True)
    if result.returncode != 0:
        raise RuntimeError(f"Copilot CLI failed with exit code {result.returncode}:\n{result.stderr}\n{result.stdout}")
    if output_path.exists():
        return extract_json(output_path.read_text(encoding="utf-8"), require_sections=True)
    if result.stdout.strip():
        print("warning: research pass did not write JSON; running synthesis recovery pass")
        return recover_report_json(result.stdout, output_path, dates)
    raise RuntimeError(f"Copilot CLI did not create expected JSON file: {output_path}")



def translate_report(report: dict, dates: dict) -> dict:
    output_path = Path(os.environ.get("COPILOT_TRANSLATION_OUTPUT_PATH", ".copilot-output/report.pl.json"))
    prompt = (
        f"{load_translation_prompt()}\n\n"
        f"Date: {dates['date']}\n\n"
        f"Translate this JSON report to Polish and write the translated JSON object to {output_path}.\n"
        "Do not edit any other files. Do not use web search. Do not write Markdown.\n\n"
        f"{json.dumps(report, ensure_ascii=False)}"
    )
    translated = run_copilot_json(prompt, output_path, allow_urls=False, require_sections=True)
    return merge_translation(report, translated)


def run_agent(dates: dict) -> dict:
    print("running compact section research fleet...", flush=True)
    research_packs = run_section_research_fleet(dates)
    print("running editor synthesis...")
    report = run_editor_report(research_packs, dates)
    report = strip_unverified_article_images(report, research_packs)
    errors = validate_final_report(report, research_packs)
    if errors:
        print("warning: editor output failed validation; running one correction pass")
        report = run_editor_report(research_packs, dates, errors)
        report = strip_unverified_article_images(report, research_packs)
        errors = validate_final_report(report, research_packs)
    if errors:
        raise RuntimeError("Final report failed validation:\n" + "\n".join(errors))
    return report


def merge_translation(report: dict, translated: dict) -> dict:
    merged = deepcopy(report)
    for key in ("title", "tagline", "breaking"):
        if isinstance(translated.get(key), str):
            merged[key] = translated[key]

    translated_sections = translated.get("sections", [])
    for section_index, section in enumerate(merged.get("sections", [])):
        if section_index >= len(translated_sections):
            break
        translated_section = translated_sections[section_index]
        if isinstance(section.get("summary"), dict) and isinstance(translated_section.get("summary"), dict):
            if translated_section["summary"].get("text"):
                section["summary"]["text"] = translated_section["summary"]["text"]
        translated_articles = translated_section.get("articles", [])
        for article_index, article in enumerate(section.get("articles", [])):
            if article_index >= len(translated_articles):
                break
            translated_article = translated_articles[article_index]
            for key in ("title", "subtitle", "facts", "body", "implications"):
                if key in translated_article:
                    article[key] = translated_article[key]
            if isinstance(article.get("stats"), list) and isinstance(translated_article.get("stats"), list):
                for stat_index, stat in enumerate(article["stats"]):
                    if stat_index < len(translated_article["stats"]) and translated_article["stats"][stat_index].get("label"):
                        stat["label"] = translated_article["stats"][stat_index]["label"]
            if isinstance(article.get("quote"), dict) and isinstance(translated_article.get("quote"), dict):
                if translated_article["quote"].get("text"):
                    article["quote"]["text"] = translated_article["quote"]["text"]
            if isinstance(article.get("claims"), list) and isinstance(translated_article.get("claims"), list):
                for claim_index, claim in enumerate(article["claims"]):
                    if claim_index < len(translated_article["claims"]) and translated_article["claims"][claim_index].get("text"):
                        claim["text"] = translated_article["claims"][claim_index]["text"]
    return merged


def section_meta(section: dict, lang: str = "en") -> dict:
    section_id = section.get("id") or "custom"
    defaults = SECTION_CONFIG.get(section_id, {})
    if defaults:
        return {
            "id": section_id,
            "title": SECTION_TITLES.get(lang, SECTION_TITLES["en"]).get(section_id, defaults["title"]),
            "icon": defaults["icon"],
            "color": defaults["color"],
            "badge": defaults["badge"],
            "visual": defaults["visual"],
        }
    return {
        "id": section_id,
        "title": section.get("title") or section_id.replace("-", " ").title(),
        "icon": section.get("icon") or "newspaper",
        "color": section.get("color") or "#374151",
        "badge": "custom",
        "visual": "".join(word[0] for word in section_id.split("-") if word)[:3].upper() or "AI",
    }


def ordered_sections(report: dict) -> list[dict]:
    sections = [section for section in report.get("sections", []) if section.get("id")]
    known = {section.get("id"): section for section in sections if section.get("id") in SECTION_CONFIG}
    ordered = [known.get(section_id, {"id": section_id, "articles": []}) for section_id in SECTION_ORDER]
    ordered.extend(section for section in sections if section.get("id") not in SECTION_CONFIG)
    return ordered


def article_class(index: int, total: int) -> str:
    if total == 1:
        return "full"
    if index == 0:
        return "featured"
    if index == 1:
        return "secondary"
    return "standard"


def domain_from_url(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc or parsed.path.split("/")[0]


def is_http_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def extract_meta_image(page_html: str, base_url: str) -> str:
    patterns = [
        r'<meta[^>]+(?:property|name)=["\']og:image(?::secure_url)?["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']og:image(?::secure_url)?["\']',
        r'<meta[^>]+(?:property|name)=["\']twitter:image(?::src)?["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']twitter:image(?::src)?["\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, page_html, flags=re.IGNORECASE)
        if not match:
            continue
        image_url = html.unescape(match.group(1).strip())
        resolved = urljoin(base_url, image_url)
        if is_http_url(resolved):
            return resolved
    return ""


def fetch_source_preview_image(source_url: str) -> str:
    if not is_http_url(source_url):
        return ""
    if source_url in IMAGE_CACHE:
        return IMAGE_CACHE[source_url]

    request = Request(
        source_url,
        headers={
            "User-Agent": "AI-Daily/1.0 (+https://github.com/Raff-dev/ai-daily)",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    try:
        with urlopen(request, timeout=10) as response:
            content_type = response.headers.get("content-type", "")
            if "html" not in content_type:
                IMAGE_CACHE[source_url] = ""
                return ""
            page_html = response.read(750_000).decode("utf-8", errors="replace")
    except (OSError, UnicodeError) as error:
        print(f"warning: could not fetch preview image metadata for {source_url}: {error}")
        IMAGE_CACHE[source_url] = ""
        return ""

    image_url = extract_meta_image(page_html, source_url)
    IMAGE_CACHE[source_url] = image_url
    if not image_url:
        print(f"warning: no OpenGraph/Twitter preview image found for {source_url}")
    return image_url


def article_image_url(article: dict) -> str:
    image_url = str(article.get("image_url") or "").strip()
    if is_http_url(image_url):
        return image_url
    return fetch_source_preview_image(str(article.get("source_url") or ""))


def render_stats(stats: list) -> str:
    if not stats:
        return ""
    items = "\n".join(
        f'<div class="stat-highlight"><span class="stat-number">{e(s.get("number"))}</span>'
        f'<span class="stat-label">{e(s.get("label"))}</span></div>'
        for s in stats
    )
    return f'<div class="stat-row">{items}</div>'


def render_badges(meta: dict, importance: str, verified: bool) -> str:
    verified_badge = "" if verified else (
        '<span class="badge badge-unverified"><i data-lucide="alert-triangle"></i> UNVERIFIED</span>'
    )
    return (
        f'<div class="card-tags">'
        f'<span class="badge badge-{e(meta["badge"])}"><i data-lucide="{e(meta["icon"])}"></i> {e(meta["title"])}</span>'
        f'<span class="badge badge-{e(importance)}"><i data-lucide="sparkles"></i> {e(importance)}</span>'
        f'{verified_badge}'
        f'</div>'
    )


def render_card_image(article: dict, meta: dict) -> str:
    image_url = article_image_url(article)
    image_html = ""
    image_class = ""
    if image_url:
        image_class = " has-image"
        image_html = (
            f'<img class="card-image" src="{e(image_url)}" alt="" loading="lazy" referrerpolicy="no-referrer" '
            "onerror=\"this.remove(); this.parentElement.classList.remove('has-image');\">"
        )
    return f"""
<div class="card-image-placeholder{image_class}" style="--accent: {e(meta["color"])};">
  {image_html}
  <svg class="card-visual-svg" viewBox="0 0 640 280" role="img" aria-label="{e(meta["title"])} visual" xmlns="http://www.w3.org/2000/svg">
    <circle cx="86" cy="76" r="42" fill="currentColor" opacity=".10"/>
    <circle cx="544" cy="214" r="58" fill="currentColor" opacity=".12"/>
    <path d="M110 205 C210 115, 330 265, 505 92" fill="none" stroke="currentColor" stroke-width="18" stroke-linecap="round" opacity=".18"/>
    <path d="M140 86 H500" stroke="currentColor" stroke-width="2" opacity=".20"/>
    <path d="M140 194 H500" stroke="currentColor" stroke-width="2" opacity=".16"/>
    <text x="320" y="154" text-anchor="middle" class="card-visual-label">{e(meta["visual"])}</text>
  </svg>
</div>"""


def render_article(article: dict, meta: dict, index: int, total: int, lang: str) -> str:
    copy = UI_COPY[lang]
    importance = article.get("importance") or "info"
    if importance not in {"breakthrough", "important", "info"}:
        importance = "info"
    badges_html = render_badges(meta, importance, article.get("verified", True))
    stats_html = render_stats(article.get("stats", []))
    image_html = render_card_image(article, meta)

    facts = "\n".join(f"<li>{e(fact)}</li>" for fact in article.get("facts", []) if fact)
    facts_html = f'<ul class="bullet-list">{facts}</ul>' if facts else ""
    body = "\n".join(f'<p class="body-text">{e(paragraph)}</p>' for paragraph in article.get("body", []) if paragraph)

    quote = article.get("quote") or {}
    quote_html = ""
    if quote.get("text"):
        quote_html = (
            f'<blockquote class="article-quote"><p>"{e(quote.get("text"))}"</p>'
            f'<cite>{e(quote.get("cite"))}</cite></blockquote>'
        )

    implications = ""
    if article.get("implications"):
        implications = (
            f'<p class="body-text implications"><i data-lucide="lightbulb"></i> '
            f'<strong>{e(copy["implications"])}:</strong> {e(article.get("implications"))}</p>'
        )

    article_sources = article.get("sources") if isinstance(article.get("sources"), list) else []
    if article_sources:
        source_links = []
        for source in article_sources[:3]:
            source_url = source.get("url") or source.get("canonical_url") or "#"
            source_name = source.get("name") or source.get("publisher") or source.get("title") or domain_from_url(source_url) or "Source"
            domain = domain_from_url(source_url)
            source_links.append(
                f'<a href="{e(source_url)}" class="source-link" target="_blank" rel="noopener">'
                f'<img src="https://www.google.com/s2/favicons?domain={e(domain)}&sz=16" alt="">'
                f'{e(source_name)}</a>'
            )
        source_html = "".join(source_links)
    else:
        source_url = article.get("source_url") or "#"
        source_name = article.get("source_name") or domain_from_url(source_url) or "Source"
        domain = domain_from_url(source_url)
        source_html = (
            f'<a href="{e(source_url)}" class="source-link" target="_blank" rel="noopener">'
            f'<img src="https://www.google.com/s2/favicons?domain={e(domain)}&sz=16" alt="">'
            f'{e(source_name)}</a>'
        )

    return f"""
<details class="news-card {article_class(index, total)}">
  <summary class="card-summary">
    {image_html}
    <div class="card-summary-content">
      {badges_html}
      <h2 class="article-title">{e(article.get("title"))}</h2>
      <p class="article-deck">{e(article.get("subtitle"))}</p>
      {stats_html}
      <span class="expand-hint">{e(copy["expand"])} <i data-lucide="chevron-down"></i></span>
    </div>
  </summary>
  <div class="card-details">
    {facts_html}
    <div class="extended-content">
      {body}
      {quote_html}
      {implications}
    </div>
    <div class="card-footer">
      {source_html}
      <span class="pub-time">{e(article.get("published_at"))}</span>
    </div>
  </div>
</details>"""


def render_section(section: dict, lang: str) -> str:
    copy = UI_COPY[lang]
    meta = section_meta(section, lang)
    articles = [article for article in section.get("articles", []) if article.get("title")]
    if articles:
        rendered_articles = "\n".join(render_article(article, meta, index, len(articles), lang) for index, article in enumerate(articles))
    else:
        rendered_articles = f'<div class="empty-section">{e(copy["empty_section"])}</div>'
    count_label = copy["article_singular"] if len(articles) == 1 else copy["article_plural"]
    return f"""
<section class="news-section" id="{e(lang)}-{e(meta["id"])}">
  <div class="section-header">
    <span class="section-icon"><i data-lucide="{e(meta["icon"])}"></i></span>
    <div class="section-meta">
      <span class="section-overline">{e(copy["section"])}</span>
      <h2 class="section-title">{e(meta["title"])}</h2>
    </div>
    <span class="section-count">{len(articles)} {count_label}</span>
  </div>
  <div class="section-divider" style="background: {e(meta["color"])};"></div>
  <div class="articles-grid">
    {rendered_articles}
  </div>
</section>"""


def collect_sources(report: dict, lang: str = "en") -> list[dict]:
    indexed_sources = report.get("source_index") if isinstance(report.get("source_index"), list) else []
    if indexed_sources:
        grouped: dict[str, list[dict]] = {}
        for source in indexed_sources:
            source_url = source.get("canonical_url") or source.get("url")
            if not source_url:
                continue
            section_id = source.get("section") if source.get("section") in SECTION_CONFIG else "source-index"
            grouped.setdefault(section_id, []).append(
                {
                    "name": source.get("publisher") or source.get("name") or source.get("title") or domain_from_url(source_url),
                    "url": source_url,
                }
            )
        sources = []
        for section_id in SECTION_ORDER:
            items = grouped.pop(section_id, [])
            if items:
                meta = section_meta({"id": section_id}, lang)
                sources.append({"title": meta["title"], "icon": meta["icon"], "items": items})
        for section_id, items in grouped.items():
            if items:
                sources.append({"title": "Source Index", "icon": "paperclip", "items": items})
        if sources:
            return sources

    sources = []
    for section in ordered_sections(report):
        meta = section_meta(section, lang)
        items = []
        for article in section.get("articles", []):
            if isinstance(article.get("sources"), list):
                for source in article["sources"]:
                    source_url = source.get("url") or source.get("canonical_url")
                    if source_url:
                        items.append({"name": source.get("name") or source.get("publisher") or source.get("title") or domain_from_url(source_url), "url": source_url})
            elif article.get("source_url"):
                items.append({"name": article.get("source_name") or domain_from_url(article["source_url"]), "url": article["source_url"]})
        if items:
            sources.append({"title": meta["title"], "icon": meta["icon"], "items": items})
    return sources


def render_sources(report: dict, lang: str) -> str:
    sections = []
    for source_section in collect_sources(report, lang):
        links = "\n".join(
            f'<li><a href="{e(item["url"])}" target="_blank" rel="noopener">{e(item["name"])}</a></li>'
            for item in source_section["items"]
        )
        sections.append(
            f'<div class="sources-section"><h4><i data-lucide="{e(source_section["icon"])}"></i> '
            f'{e(source_section["title"])}</h4><ul>{links}</ul></div>'
        )
    return "\n".join(sections)


def render_nav(report: dict, lang: str) -> str:
    links = []
    for section in ordered_sections(report):
        meta = section_meta(section, lang)
        if section.get("articles"):
            links.append(f'<a href="#{e(lang)}-{e(meta["id"])}"><i data-lucide="{e(meta["icon"])}"></i> {e(meta["title"])}</a>')
    links.append(f'<a href="#{e(lang)}-sources"><i data-lucide="paperclip"></i> {e(UI_COPY[lang]["sources"])}</a>')
    return "\n".join(links)


def get_repo_url() -> str:
    gh_repo = os.environ.get("GITHUB_REPOSITORY", "")
    if gh_repo:
        return f"https://github.com/{gh_repo}"
    try:
        remote = subprocess.check_output(
            ["git", "remote", "get-url", "origin"], stderr=subprocess.DEVNULL, text=True
        ).strip()
        if remote.startswith("https://github.com/"):
            return remote.rstrip(".git")
        if remote.startswith("git@github.com:"):
            path = remote.replace("git@github.com:", "").rstrip(".git")
            return f"https://github.com/{path}"
    except Exception:
        pass
    return "https://github.com/Raff-dev/ai-daily"


def render_language_toggle(active_lang: str, has_translation: bool) -> str:
    buttons = []
    languages = (("en", "EN"), ("pl", "PL")) if has_translation else (("en", "EN"),)
    for lang, label in languages:
        active = " active" if lang == active_lang else ""
        buttons.append(f'<button type="button" class="{active.strip()}" data-set-lang="{lang}">{label}</button>')
    return f'<div class="language-toggle" aria-label="Language">{"".join(buttons)}</div>'


def render_report_panel(report: dict, dates: dict, lang: str, active: bool, has_translation: bool) -> str:
    copy = UI_COPY[lang]
    report_sections = ordered_sections(report)
    sections = [render_section(section, lang) for section in report_sections]
    sections_html = "\n".join(section for section in sections if section)
    section_count = len(report_sections)
    source_count = sum(len(source["items"]) for source in collect_sources(report, lang))
    articles_count = sum(len(section.get("articles", [])) for section in report_sections)
    reviewed = report.get("articles_reviewed") or articles_count
    tagline = report.get("tagline") or "Everything you need to know from the last 24 hours."
    day_label = dates.get("day_pl", dates["day"]) if lang == "pl" else dates["day"]
    date_long = dates.get("date_long_pl", dates["date_long"]) if lang == "pl" else dates["date_long"]
    date_short = dates.get("date_short_pl", dates["date_short"]) if lang == "pl" else dates["date_short"]
    breaking = ""
    if report.get("breaking"):
        breaking = (
            f'<div class="breaking-banner" role="alert">'
            f'<span class="breaking-tag"><i data-lucide="zap"></i> {e(copy["breaking"])}</span>{e(report["breaking"])}</div>'
        )

    active_class = " active" if active else ""
    return f"""
<div class="language-panel{active_class}" data-lang="{e(lang)}">
<header class="masthead">
  <div class="masthead-inner">
    <div class="masthead-brand">
      <span class="masthead-title">{e(report.get("title") or "AI Daily")}</span>
      <span class="masthead-edition">{e(date_short)}</span>
    </div>
    <nav class="masthead-nav">{render_nav(report, lang)}</nav>
    {render_language_toggle(lang, has_translation)}
    <a href="{e(get_repo_url())}" class="masthead-github" target="_blank" rel="noopener" title="Source on GitHub"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2C6.477 2 2 6.484 2 12.021c0 4.428 2.865 8.185 6.839 9.504.5.092.682-.217.682-.483 0-.237-.009-.868-.013-1.703-2.782.605-3.369-1.342-3.369-1.342-.454-1.156-1.11-1.463-1.11-1.463-.908-.62.069-.608.069-.608 1.004.07 1.532 1.032 1.532 1.032.891 1.529 2.341 1.088 2.91.832.091-.647.349-1.088.635-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0 1 12 6.844a9.59 9.59 0 0 1 2.504.337c1.909-1.296 2.747-1.026 2.747-1.026.546 1.378.202 2.397.1 2.65.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482C19.138 20.203 22 16.447 22 12.021 22 6.484 17.523 2 12 2z"/></svg></a>
    <span class="masthead-version">{e(copy["structured"])}</span>
  </div>
</header>
<div class="hero-header">
  <div class="hero-inner">
    <div class="hero-date">{e(day_label)}, {e(date_long)} · {e(copy["edition"])}</div>
    <h1 class="hero-title">{copy["hero"]}</h1>
    <p class="hero-tagline">{e(tagline)}</p>
    <div class="hero-stats">
      <div class="hero-stat-item"><span class="hero-stat-num">{e(reviewed)}</span><span class="hero-stat-label">{e(copy["articles_reviewed"])}</span></div>
      <div class="hero-stat-item"><span class="hero-stat-num">{section_count}</span><span class="hero-stat-label">{e(copy["topic_sections"])}</span></div>
      <div class="hero-stat-item"><span class="hero-stat-num">{source_count}</span><span class="hero-stat-label">{e(copy["verified_sources"])}</span></div>
    </div>
  </div>
</div>
<div class="page-wrapper">
  {breaking}
  {sections_html}
  <footer class="report-footer" id="{e(lang)}-sources">
    <h3 class="footer-title"><i data-lucide="paperclip"></i> {e(copy["sources"])}</h3>
    <div class="sources-grid">{render_sources(report, lang)}</div>
    <div class="footer-meta">
      <p><i data-lucide="cpu"></i> {e(copy["footer_generated"])}: {e(dates["datetime"])} {e(copy["footer_renderer"])}</p>
      <p><i data-lucide="clock"></i> {e(copy["footer_window"])}</p>
      <p><i data-lucide="bar-chart-2"></i> {e(copy["footer_sources"])}: {source_count}</p>
      <p><i data-lucide="file-text"></i> {e(copy["footer_output"])}</p>
    </div>
  </footer>
</div>
</div>"""


def render_report(report: dict, dates: dict, translated_report: dict | None = None) -> str:
    has_translation = translated_report is not None
    panels = [render_report_panel(report, dates, "en", active=True, has_translation=has_translation)]
    if translated_report:
        panels.append(render_report_panel(translated_report, dates, "pl", active=False, has_translation=has_translation))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(report.get("title") or "AI Daily")} — {e(dates["date_long"])}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<script src="https://unpkg.com/lucide@latest/dist/umd/lucide.min.js"></script>
<style>{REPORT_CSS}</style>
</head>
<body data-render-version="compact-research-v1">
{''.join(panels)}
<script>
const setLanguage = (lang) => {{
  document.documentElement.lang = lang;
  document.querySelectorAll('.language-panel').forEach((panel) => {{
    panel.classList.toggle('active', panel.dataset.lang === lang);
  }});
  document.querySelectorAll('[data-set-lang]').forEach((button) => {{
    button.classList.toggle('active', button.dataset.setLang === lang);
  }});
  localStorage.setItem('ai-daily-lang', lang);
  if (window.lucide) window.lucide.createIcons();
}};
document.querySelectorAll('[data-set-lang]').forEach((button) => {{
  button.addEventListener('click', () => setLanguage(button.dataset.setLang));
}});
const storedLanguage = localStorage.getItem('ai-daily-lang') || 'en';
setLanguage(document.querySelector(`.language-panel[data-lang="${{storedLanguage}}"]`) ? storedLanguage : 'en');
</script>
</body>
</html>"""


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

    html_doc = f"""<!DOCTYPE html>
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
  <p class="sub">Daily news briefing — generated automatically every morning.</p>
  <ul>
{items}
  </ul>
</div>
</body>
</html>"""

    Path("index.html").write_text(html_doc, encoding="utf-8")
    print("updated index.html")


def report_is_current_format(output_path: Path) -> bool:
    if not output_path.exists():
        return False
    html_doc = output_path.read_text(encoding="utf-8")
    return 'data-lang="pl"' in html_doc and 'data-render-version="compact-research-v1"' in html_doc


def main() -> None:
    dates = get_date_info()
    print(f"generating AI Daily Brief for {dates['date']}...")

    outputs_dir = Path("outputs")
    outputs_dir.mkdir(exist_ok=True)

    output_path = outputs_dir / f"AI_Daily_{dates['date']}.html"
    if output_path.exists() and report_is_current_format(output_path):
        print(f"bilingual report already exists: {output_path} — skipping generation")
    else:
        report = run_agent(dates)
        translated_report = translate_report(report, dates)
        output_path.write_text(render_report(report, dates, translated_report), encoding="utf-8")
        print(f"saved {output_path}")

    rebuild_index(outputs_dir)


if __name__ == "__main__":
    main()
