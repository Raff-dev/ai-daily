#!/usr/bin/env python3
"""AI Daily Brief — asks an agent for structured content and renders stable HTML."""

import html
import json
import os
import re
import subprocess
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
    "ai-tools": {"title": "AI Tools", "icon": "sparkles", "color": "#DB2777", "badge": "ai-tool", "visual": "AI"},
    "robotics": {"title": "Robotics", "icon": "bot", "color": "#16A34A", "badge": "robot", "visual": "BOT"},
    "defense": {"title": "Defense", "icon": "shield", "color": "#DC2626", "badge": "defense", "visual": "DEF"},
    "space": {"title": "Space", "icon": "rocket", "color": "#7C3AED", "badge": "space", "visual": "ORB"},
    "startups": {"title": "Startups", "icon": "banknote", "color": "#EA580C", "badge": "startup", "visual": "CAP"},
    "markets": {"title": "Markets", "icon": "bar-chart-2", "color": "#0F766E", "badge": "market", "visual": "MKT"},
}
SECTION_ORDER = tuple(SECTION_CONFIG)
COPILOT_MODEL = "gpt-5.4"
IMAGE_CACHE: dict[str, str] = {}

SECTION_TITLES = {
    "en": {
        "dev-tools": "Developer Tools",
        "ai-tools": "AI Tools",
        "robotics": "Robotics",
        "defense": "Defense",
        "space": "Space",
        "startups": "Startups",
        "markets": "Markets",
    },
    "pl": {
        "dev-tools": "Narzędzia developerskie",
        "ai-tools": "Narzędzia AI",
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

Use the repository owner's custom brief from agent.md. If it conflicts with default topics,
the custom brief wins.

Process:
1. Run the searches requested by agent.md, replacing {DATE}, {YEAR}, and {MONTH}.
2. Keep only news published in the last 24 hours.
3. Use only these section ids, in this exact order: dev-tools, ai-tools, robotics, defense, space, startups, markets.
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

Allowed default section ids: dev-tools, ai-tools, robotics, defense, space, startups, markets.
AI Tools is for non-coding AI products and apps; do not put developer harnesses, coding agents, IDEs, or SDKs there.
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


def load_agent_prompt() -> str:
    prompt_path = Path(os.environ.get("AGENT_PROMPT_PATH", "agent.md"))
    if not prompt_path.exists():
        raise FileNotFoundError(f"Agent prompt file not found: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8").strip()


def load_translation_prompt() -> str:
    prompt_path = Path(os.environ.get("TRANSLATION_PROMPT_PATH", "translate-agent.md"))
    if not prompt_path.exists():
        raise FileNotFoundError(f"Translation prompt file not found: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8").strip()


def build_system_prompt() -> str:
    return f"{SYSTEM_PROMPT}\n\n## CUSTOM AGENT BRIEF FROM agent.md\n\n{load_agent_prompt()}"


def build_user_message(dates: dict) -> str:
    return (
        f"Generate today's structured AI Daily Brief content.\n\n"
        f"Date: {dates['date']}\n"
        f"Day: {dates['day']}\n"
        f"Month: {dates['month']}\n"
        f"Year: {dates['year']}\n\n"
        "Return JSON only. The app will render HTML."
    )


def extract_json(text: str) -> dict:
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
    if not isinstance(data.get("sections"), list):
        raise RuntimeError("Agent JSON must contain a 'sections' array.")
    return data


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
        "--model",
        COPILOT_MODEL,
        "--no-ask-user",
    ]
    if allow_urls:
        command.append("--allow-all-urls")

    return subprocess.run(
        command,
        text=True,
        capture_output=True,
        timeout=int(os.environ.get("AGENT_TIMEOUT_SECONDS", "1800")),
        check=False,
    )


def run_copilot_json(prompt: str, output_path: Path, allow_urls: bool) -> dict:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()

    result = invoke_copilot(prompt, output_path, allow_urls)
    if result.returncode != 0:
        raise RuntimeError(f"Copilot CLI failed with exit code {result.returncode}:\n{result.stderr}\n{result.stdout}")
    if not output_path.exists():
        raise RuntimeError(f"Copilot CLI did not create expected JSON file: {output_path}\n{result.stdout}")
    return extract_json(output_path.read_text(encoding="utf-8"))


def recover_report_json(research_notes: str, output_path: Path, dates: dict) -> dict:
    notes = research_notes[-55_000:]
    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        "You are the synthesis pass for AI Daily. The research pass produced notes but failed to write JSON.\n"
        f"Date: {dates['date']}\n\n"
        "Convert the research notes below into the required final JSON object.\n"
        "Use only facts present in the notes. Do not use web search. Do not add Markdown or explanations.\n"
        "Return every canonical section id: dev-tools, ai-tools, robotics, defense, space, startups, markets. Prefer 3-4 articles per section, but do not drop a section solely because it has fewer candidates.\n"
        f"Write the final JSON object to {output_path} and do not edit any other files.\n\n"
        f"## RESEARCH NOTES\n\n{notes}"
    )
    return run_copilot_json(prompt, output_path, allow_urls=False)


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
        return extract_json(output_path.read_text(encoding="utf-8"))
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
    translated = run_copilot_json(prompt, output_path, allow_urls=False)
    return merge_translation(report, translated)


def run_agent(dates: dict) -> dict:
    return run_copilot_agent(dates, build_system_prompt())


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
    sources = []
    for section in ordered_sections(report):
        meta = section_meta(section, lang)
        items = []
        for article in section.get("articles", []):
            if article.get("source_url"):
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
<body data-render-version="source-images-v4">
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
    return 'data-lang="pl"' in html_doc and 'data-render-version="source-images-v4"' in html_doc


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
