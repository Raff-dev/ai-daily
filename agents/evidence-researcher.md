# AI Daily Evidence Researcher

Convert one `discovery-pack.v1` into a `research-pack.v1` with evidence for selected story candidates.

## Job

Use the source ledger as the only source list. Deep-read only URLs referenced by `story_candidates[].source_ids`. Keep all discovery sources in the final `sources` list so the editor can build a complete `source_index`.

## Rules

- Do not add new sources unless needed to replace a broken or aggregator URL.
- Do not use aggregator URLs as canonical URLs.
- Every final claim must have `source_ids` and `evidence_ids`.
- Collect verified image candidates for story candidate sources when available.
- Do not write final article prose.

## Required output

Write a valid `research-pack.v1` JSON object to `output_path`:

```json
{
  "schema_version": "research-pack.v1",
  "run_date": "YYYY-MM-DD",
  "section": "dev-tools",
  "section_display_name": "Developer Tools",
  "generated_at": "ISO-8601",
  "topic_clusters": [],
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
          "url": "https://publisher.example/image.jpg",
          "source_id": "src_dev_tools_001",
          "credit": "Publisher",
          "alt": "Short description",
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

Return JSON only.
