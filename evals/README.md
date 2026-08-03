# PRD quality evals

This directory separates two different claims that must not be conflated:

1. **Deterministic contract checks** inspect a pre-authored artifact for structure, traceability, unsupported numeric claims, open questions, Outcome Contracts, and the PRD/Implementation Plan boundary.
2. **Model-quality evaluation** would ask an agent to produce an artifact from fixed inputs and score the result with the versioned rubric. This repository does not ship or invoke a model runtime, so that result is not claimed here.

The four golden cases exercise different product judgment:

| Case | Product pressure |
|---|---|
| `b2c-ux` | Directional usability evidence without a measured prevalence or baseline |
| `b2b-arr-demand` | Customer demand weighted by source-backed ARR without turning ARR into automatic priority |
| `evidence-waiver` | A deliberate decision to proceed without sufficient evidence, with explicit risk and review conditions |
| `multi-prd-initiative-routing` | One shared outcome routed into distinct child PRDs without putting child requirements in the Initiative |

Run the deterministic layer:

```bash
python evals/check_prd_quality.py
python -m pytest tests/evals
```

Passing means only that the checked documents satisfy the versioned structural contract. It does not prove that an LLM asked good questions, chose the right problem, wrote persuasive prose, or produced a better product decision.

## Future model-eval protocol

A model runtime may later use the same `case.yaml` inputs without access to `golden/`, then:

1. generate the requested PRD or Initiative set;
2. run this deterministic contract first;
3. score the surviving output against `prd-quality-rubric.yaml` with fixed model/version/settings;
4. retain per-dimension evidence and all unsupported-claim findings;
5. require human adjudication for product judgment and any proposed release gate.

Scores from different models or rubric versions are not comparable unless the case set, prompt, judge, and settings are identical.
