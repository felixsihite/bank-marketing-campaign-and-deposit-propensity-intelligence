# Data Quality Report

## Executive Status

**PASS** - Source schema, row count, null policy, target domain, numeric ranges, and source-to-output grain were validated.

| Check | Result | Treatment |
|---|---:|---|
| Source observations | 41,188 | Retained |
| Source columns | 21 | Matches contract |
| Native null cells | 0 | None introduced |
| Exact duplicate excess rows | 12 | Retained and explicitly flagged |
| Positive observations | 4,640 | Target preserved |
| Positive rate | 11.27% | Imbalance handled in modeling |
| `pdays = 999` | 39,673 | Retained as documented not-previously-contacted sentinel |

## Unknown Category Audit

`unknown` is a source category, not a native null. It is retained to avoid unjustified imputation.

| Field | Unknown observations |
|---|---:|
| `job` | 330 |
| `marital` | 80 |
| `education` | 1,731 |
| `default` | 8,597 |
| `housing` | 990 |
| `loan` | 990 |

## Duplicate Decision

All 41,188 source observations are retained because there is no unique customer or campaign identifier capable of proving that identical rows are erroneous. The pipeline adds technical flags for 12 excess duplicate rows. This preserves the stated fact-table grain: **one row per source campaign observation**.

## Outlier Policy

Extreme values such as age 98, campaign contacts 56, and duration 4,918 seconds are profiled but not automatically removed. `duration` is available only for retrospective post-call analysis and is excluded from the production propensity model.

## Source Integrity

SHA-256: `74adfc578bf77a7ff4bb1ba4a9f8709d9e3c6907342959c2c8416847e0afb4d8`
