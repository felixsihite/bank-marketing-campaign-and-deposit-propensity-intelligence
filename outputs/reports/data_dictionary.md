# Data Dictionary

| Field | Type | Business definition |
|---|---|---|
| `campaign_record_id` | Integer | Technical surrogate for a source campaign observation; not a customer ID. |
| `age` | Integer | Age in years. |
| `job` | Category | Occupation category. |
| `marital` | Category | Marital status. |
| `education` | Category | Detailed education category. |
| `default` | Category | Credit default status, including unknown. |
| `housing` | Category | Housing-loan status, including unknown. |
| `loan` | Category | Personal-loan status, including unknown. |
| `contact` | Category | Campaign contact channel. |
| `month` | Category | Last-contact month; year unavailable. |
| `day_of_week` | Category | Last-contact weekday. |
| `duration` | Integer | Last call duration in seconds; retrospective use only, excluded from propensity model. |
| `campaign` | Integer | Contacts during the current campaign for this observation. |
| `pdays` | Integer | Days since prior campaign contact; 999 means not previously contacted. |
| `previous` | Integer | Contacts before the current campaign. |
| `poutcome` | Category | Outcome of the previous campaign. |
| `emp.var.rate` | Decimal | Employment variation rate. |
| `cons.price.idx` | Decimal | Consumer price index. |
| `cons.conf.idx` | Decimal | Consumer confidence index. |
| `euribor3m` | Decimal | Three-month Euribor rate. |
| `nr.employed` | Decimal | Number employed indicator. |
| `y` | Binary category | Whether a term deposit was subscribed. |
| `conversion_flag` | Binary integer | 1 when y=yes, otherwise 0. |
| `propensity_score` | Decimal | Final-model operational ranking score across the historical portfolio. |
| `propensity_decile` | Integer | Operational score rank; not an unbiased evaluation metric. |
| `locked_test_decile` | Integer | Evaluation-only decile derived from locked-test probabilities. |

Derived segmentation fields are deterministic, documented in `src/bank_intelligence/features.py`, and contain no fabricated outcomes.
