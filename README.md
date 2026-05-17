# 🗞️ AI Daily

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Daily AI Brief](https://github.com/Raff-dev/ai-daily/actions/workflows/daily.yml/badge.svg)](https://github.com/Raff-dev/ai-daily/actions/workflows/daily.yml)

> Your personal AI news briefing, delivered every morning — fully automated, no server needed.

An AI agent wakes up every day at 6 AM, searches the web for the latest news, verifies sources, and publishes a polished HTML report to your GitHub Pages. You just read it with your coffee ☕

**👉 Live example:** [`raff-dev.github.io/ai-daily`](https://raff-dev.github.io/ai-daily)

---

## ✨ What it does

- 🔍 Searches the web for news from the last 24 hours
- 🤖 Runs a fleet of agents: one per topic section, then an editor, then a translator
- ✅ Verifies sources and filters out aggregators
- 🇵🇱 Generates both English and Polish versions with a toggle
- 📰 Publishes a beautiful HTML report with article previews to GitHub Pages
- 💤 Your laptop can be completely off — it all runs in the cloud

![AI Daily screenshot](https://raff-dev.github.io/ai-daily/outputs/preview.png)

---

## 🚀 Get started in 4 steps

### 1. Fork this repo

Click **Fork** at the top of this page. Keep it **public** — that's required for free GitHub Pages and scheduled Actions.

### 2. Create a GitHub token

You need a GitHub account with an active **Copilot** subscription. Then create a fine-grained personal access token:

```
https://github.com/settings/personal-access-tokens/new?name=AI+Daily&copilot_requests=write
```

Set **Account permissions → Copilot requests → Write**.

### 3. Add the token as a secret

In your forked repo go to **Settings → Secrets and variables → Actions → New repository secret**:

| Name | Value |
|---|---|
| `PERSONAL_ACCESS_TOKEN` | the token you just created |

### 4. Enable GitHub Pages

Go to **Settings → Pages** and set Source to **GitHub Actions**.

That's it! 🎉 The workflow runs daily at **05:00 UTC**. You can also trigger it manually from **Actions → Daily AI Brief → Run workflow**.

---

## 🎨 Make it yours

This is the fun part. Fork the repo, open it in your AI coding assistant, and just tell it what you want:

```
Download this repo and edit it so it covers only travel industry news —
flights, hotels, airline stocks, and tourism startups.
```

Your AI assistant (Claude, Codex, Copilot — all supported) will know exactly what to change because the project includes `CLAUDE.md`, `AGENTS.md`, and `.github/copilot-instructions.md` with clear instructions.

What you can change in `agent.md`:

- 📋 **Topics** — what the briefing covers
- 🔎 **Search queries** — what the agent actually searches for
- 📂 **Sections** — which categories appear in the report

Some ideas:
- 🏋️ Sports news (football transfers, Formula 1, NBA)
- 🏘️ Real estate market + mortgage rates
- 🌿 Climate & energy industry
- 💊 Biotech & pharma funding
- 🎮 Gaming industry news

---

## 💰 Cost

Each run uses GitHub Copilot premium requests from your Copilot subscription.
The HTML renderer runs on your own compute (GitHub Actions), so you're not spending tokens on layout every day.

GitHub Actions gives you **2,000 free minutes/month** on public repos — enough for the daily run with headroom to spare.

---

## 📄 License

MIT — fork it, modify it, make it yours.
