# Model Governance Report

## Evaluation Boundary

All performance, calibration, subgroup, and decile metrics in this report use the **locked test set only** (8,238 observations). Full-portfolio propensity scores are operational ranking outputs and are not used as unbiased performance evidence.

## Monitoring Summary

| Control | Result | Interpretation |
|---|---:|---|
| Expected calibration error | 0.009 | Lower is better; monitor after deployment |
| Maximum train-to-test PSI | 0.002 | Stable |
| Eligible subgroup slices | 29 | Minimum 100 observations |
| Eligible recall range | 28.5% - 99.4% | Performance variation, not proof of fairness |
| Eligible precision range | 28.0% - 68.0% | Review before operational deployment |

## Governance Boundaries

- `duration` is excluded from pre-contact modeling.
- Protected attributes are unavailable, so a complete legal or ethical fairness assessment is impossible.
- PSI compares the model-fit training split with the locked test split; production monitoring should compare a stable reference window with new scored populations.
- Historical associations and feature importance do not establish causality.
