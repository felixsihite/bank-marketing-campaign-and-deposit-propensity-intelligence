# Model Card - Deposit Propensity

## Intended Use

Rank campaign observations by pre-contact term-deposit propensity to support targeting scenarios. The score is decision support, not an automated eligibility or credit decision.

## Champion

- Model: **Gradient Boosting**
- Selection criterion: validation PR-AUC, supported by 3-fold stratified cross-validation
- Calibration: sigmoid calibration
- Recommended threshold: **0.150**, chosen by maximum validation F2
- Duration excluded: **Yes**, because it is not known before the call

## Locked Test Performance

| Metric | Value |
|---|---:|
| PR-AUC | 0.480 |
| ROC-AUC | 0.807 |
| Precision | 41.9% |
| Recall | 62.6% |
| F1 | 0.502 |
| Brier score | 0.075 |
| Top-decile conversion | 52.9% |
| Top-decile lift | 4.70x |

All decile metrics above use the locked test set only. Full-portfolio scores are operational ranking outputs and must not be presented as unbiased model evaluation.

## Limitations and Risks

- No customer ID, transaction history, campaign cost, revenue, or profit data.
- Rows are campaign observations, not verified unique customers.
- No full calendar date or year field; seasonality cannot be separated cleanly from year effects.
- Scores reflect historical associations and do not establish causality.
- Monitor population drift, calibration, subgroup performance, and operational capacity before deployment.
