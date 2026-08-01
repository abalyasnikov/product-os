---
schema_version: 1
id: update_<stable-id>
type: product_update
title: <period> product update
relationships:
  learnings: [learning_<id>]
period_start: <YYYY-MM-DD>
period_end: <YYYY-MM-DD>
audience: <audience>
claims:
  - claim: <material claim>
    source_references:
      - kind: artifact
        artifact_id: learning_<id>
        version: <approved-git-version>
---

## Update

Write the narrative here. Every material claim must have a frontmatter source reference.
