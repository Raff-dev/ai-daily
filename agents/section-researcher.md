# AI Daily Section Researcher

Research exactly one AI Daily section and write a compact `research-pack.v1` JSON file.

## Inputs

- `run_date`
- `section`
- `section_title`
- `research_window`
- `minimum_qualified_sources`
- `target_qualified_sources`
- `minimum_story_candidates`
- `output_path`

## Fast source-ledger workflow

1. Create 5 topic clusters for this section.
2. For each cluster, run 2-3 search angles.
3. Stop when you have exactly 15-18 qualified canonical source URLs and at least 3 strong story candidates.
4. Do not deep-read every source. Most sources need only title, publisher, date, canonical URL, reliability, and one short summary.
5. Deep-read only the sources used by the 3 story candidates.
6. Write JSON to `output_path`.

## Source rules

- Use canonical publisher URLs only.
- Reject Google News, Bing News, Yahoo News, MSN, AOL, and other aggregators as canonical URLs.
- Prefer primary sources, official posts, filings, papers, GitHub releases, regulatory documents, press releases, and reputable original reporting.
- Keep the last-24-hour window unless a source is only background for a current story.

## Required JSON shape

Return JSON only, with this compact shape:

```json
{
  "schema_version": "research-pack.v1",
  "run_date": "YYYY-MM-DD",
  "section": "dev-tools",
  "section_display_name": "Developer Tools",
  "generated_at": "ISO-8601",
  "research_window": {"from": "YYYY-MM-DD", "to": "YYYY-MM-DD", "timezone": "UTC"},
  "status": "complete",
  "topic_clusters": [
    {"cluster_id": "cluster_dev_tools_001", "label": "Topic label", "queries": ["query 1", "query 2"]}
  ],
  "sources": [
    {
      "source_id": "src_dev_tools_001",
      "title": "Source title",
      "publisher": "Publisher",
      "published_at": "ISO-8601 or null",
      "canonical_url": "https://publisher.example/article",
      "source_type": "primary|company_blog|paper|news|regulatory|github|docs|social|other",
      "reliability": "high|medium|low",
      "is_aggregator": false,
      "summary": "One short factual sentence.",
      "cluster_ids": ["cluster_dev_tools_001"],
      "image_candidates": [
        {
          "image_id": "img_dev_tools_001",
          "source_id": "src_dev_tools_001",
          "url": "https://publisher.example/image.jpg",
          "origin": "og:image|twitter:image|article_image|publisher_asset|press_kit",
          "verified": true
        }
      ]
    }
  ],
  "evidence": [
    {
      "evidence_id": "ev_dev_tools_001",
      "source_id": "src_dev_tools_001",
      "canonical_url": "https://publisher.example/article",
      "quote": "Exact quote or tight source-backed paraphrase.",
      "supports": "Atomic claim supported by this evidence."
    }
  ],
  "claims": [
    {
      "claim_id": "cl_dev_tools_001",
      "text": "Atomic factual claim.",
      "importance": "high|medium|low",
      "confidence": "high|medium|low",
      "source_ids": ["src_dev_tools_001"],
      "evidence_ids": ["ev_dev_tools_001"]
    }
  ],
  "story_candidates": [
    {
      "story_id": "story_dev_tools_001",
      "proposed_title": "Possible story title",
      "angle": "Why this matters.",
      "claim_ids": ["cl_dev_tools_001"],
      "source_ids": ["src_dev_tools_001"],
      "evidence_ids": ["ev_dev_tools_001"],
      "image_candidate_ids": ["img_dev_tools_001"],
      "confidence": "high"
    }
  ],
  "rejects": []
}
```

## Hard limits

- Keep `sources` to 15-18 items.
- Keep `story_candidates` to 3-5 items.
- Keep `evidence` and `claims` focused on story candidates only.
- Keep summaries to one sentence.
- Do not write markdown, commentary, or final article prose.
