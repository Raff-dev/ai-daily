# 🗞️ AI Daily

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Daily AI Brief](https://github.com/Raff-dev/ai-daily/actions/workflows/daily.yml/badge.svg)](https://github.com/Raff-dev/ai-daily/actions/workflows/daily.yml)

> Your personal news briefing on any topic, delivered every morning — fully automated, no server needed.

An AI agent wakes up every day, searches the web for the latest news, verifies sources, and publishes a polished HTML report to your GitHub Pages. You just read it with your coffee ☕

**👉 Live example:** [`raff-dev.github.io/ai-daily`](https://raff-dev.github.io/ai-daily)

---

## 🚀 Get your own in one prompt

Open your AI coding assistant — Claude, Copilot, or Codex — paste the prompt below, and replace the topic with whatever you want. That's it.

```
Fork https://github.com/Raff-dev/ai-daily and customize it so it covers
[YOUR TOPIC] news instead of AI news. Update agent.md with relevant
search queries and section names. Then tell me exactly what I need to
do manually to make it run automatically every morning.
```

**Example topics people use this for:**
- ✈️ Travel industry — flights, hotels, airline stocks, tourism startups
- 🏋️ Sports — football transfers, Formula 1, NBA
- 💊 Biotech & pharma — FDA approvals, clinical trials, funding rounds
- 🌿 Climate & energy — renewables, carbon markets, nuclear
- 🎮 Gaming — launches, studios, esports

Your AI assistant will fork the repo, edit the right files, and walk you through the 2 remaining steps it can't do for you (adding a secret token and enabling GitHub Pages).

> **Works with:** Claude Code · GitHub Copilot · OpenAI Codex
> The repo includes `CLAUDE.md`, `AGENTS.md`, and `.github/copilot-instructions.md`
> so your assistant knows exactly what to change regardless of which tool you use.

---

## 🔑 The 2 manual steps (your AI will remind you)

Your AI assistant handles the fork and customization automatically. You only need to do these two things yourself:

### 1. Add a secret token

In your forked repo go to **Settings → Secrets and variables → Actions → New repository secret**.

You need a GitHub account with an active **Copilot** subscription. Create a fine-grained token here:

```
https://github.com/settings/personal-access-tokens/new?name=AI+Daily&copilot_requests=write
```

Set **Account permissions → Copilot requests → Write**, then add it as:

| Secret name | Value |
|---|---|
| `PERSONAL_ACCESS_TOKEN` | the token you just created |

### 2. Enable GitHub Pages

Go to **Settings → Pages**, set Source to **GitHub Actions**, and save.

That's it 🎉 The workflow runs daily at **05:00 UTC**. You can also trigger it manually from **Actions → Daily AI Brief → Run workflow**.

---

## 💰 Cost

Each run uses GitHub Copilot premium requests from your Copilot subscription — no extra billing. GitHub Actions gives you **2,000 free minutes/month** on public repos, enough for the daily run with headroom to spare.

---

## 🛠️ Manual setup (advanced)

If you prefer to set everything up yourself without an AI assistant:

```bash
git clone https://github.com/<you>/ai-daily
cd ai-daily
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PERSONAL_ACCESS_TOKEN=github_pat_...
python run.py
```

To change topics, edit `agent.md` — update the coverage list and search queries, keep everything else unchanged.

---

## 📄 License

MIT — fork it, modify it, make it yours.
