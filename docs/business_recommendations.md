# Executive Decision Support

## Observed Facts

- 4,640 of 41,188 campaign observations subscribed: 11.27% observed conversion.
- Cellular observations converted at 14.74% versus 5.23% for telephone.
- Profiles with a successful previous campaign outcome converted at 65.11%.
- Observed conversion declined from 13.03% at one current-campaign contact to 6.11% at five or more contacts.
- The 60+ age band and student occupation show high observed conversion, but volume must be reviewed before prioritization.

## Analytical Interpretations

- Previous successful engagement is the clearest profile-prioritization signal in this dataset.
- Higher contact frequency is associated with diminishing observed conversion, but selection effects may contribute.
- Month and macroeconomic patterns are strong, yet the missing year/date fields prevent clean seasonal or causal conclusions.

## Predictive Findings

- Gradient Boosting is the champion by validation PR-AUC.
- Locked-test PR-AUC is 0.480 and ROC-AUC is 0.807.
- At the 0.150 F2 threshold, recall is 62.6% and precision is 41.9%.
- Locked-test top-decile conversion is 52.9%, producing 4.70x lift over the test base rate.

## Recommended Actions

1. Start outreach capacity with top-decile and prior-success observations, then expand by propensity tier.
2. Prefer cellular when operationally eligible, while testing channel assignment through randomized holdouts.
3. Use a conservative current-campaign contact cap; investigate diminishing returns before authorizing fifth-plus attempts.
4. Treat the 0.150 threshold as a configurable capacity setting, not a universal policy.
5. Apply minimum-volume rules to profile recommendations and review subgroup precision/recall before deployment.
6. Establish experiment holdouts to measure incremental lift; historical conversion alone cannot prove campaign impact.

## Operational Risks

- No consent, affordability, complaint, channel eligibility, or contact-policy fields are available.
- The model can reproduce historical selection patterns and macroeconomic conditions.
- Scores are unsuitable for credit eligibility or adverse-action decisions.
- Production use requires monitoring for drift, calibration, fairness, and incremental performance.
