# AI Daily Source Discovery

Find sources for exactly one AI Daily section and write a compact `discovery-pack.v1` JSON file.

## Inputs

- `run_date`
- `section`
- `section_title`
- `research_window`
- `minimum_qualified_sources`
- `target_qualified_sources`
- `minimum_story_candidates`
- `output_path`

## Job

This is a breadth-first source ledger pass. Do not deep-read every source and do not write article prose.

1. Create 5 topic clusters for the section.
2. Search 2-3 query angles per cluster.
3. Return 15-18 qualified canonical source URLs.
4. Select 3-5 story candidates worth deeper evidence research.
5. Write JSON to `output_path`.

## Rules

- Use canonical publisher URLs only.
- Reject Google News, Bing News, Yahoo News, MSN, AOL, and other aggregators as canonical URLs.
- Most sources need only: title, publisher, date if available, canonical URL, reliability, source type, and one short summary.
- Do not collect detailed evidence here. Evidence is a separate pass.

## Required JSON shape

```json
{
  "schema_version": "discovery-pack.v1",
  "run_date": "YYYY-MM-DD",
  "section": "dev-tools",
  "section_display_name": "Developer Tools",
  "generated_at": "ISO-8601",
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
      "image_url": "https://publisher.example/image.jpg or null"
    }
  ],
  "story_candidates": [
    {
      "story_id": "story_dev_tools_001",
      "proposed_title": "Possible story title",
      "angle": "Why this candidate deserves deeper research.",
      "source_ids": ["src_dev_tools_001", "src_dev_tools_002"],
      "priority": 1,
      "confidence": "high|medium|low"
    }
  ],
  "rejects": []
}
```

Return JSON only.

