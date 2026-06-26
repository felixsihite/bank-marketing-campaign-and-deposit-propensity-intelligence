# Source-to-Target Reconciliation

| Layer | Rows | Status |
|---|---:|---|
| Raw source | 41,188 | Baseline |
| Processed observations | 41,188 | PASS |
| SQLite staging | 41,188 | PASS |
| Campaign fact | 41,188 | PASS |
| Propensity score mart | 41,188 | PASS |
| Orphan customer-profile keys | 0 | PASS |

Target positives reconcile to 4,640. Duplicate observations are retained and flagged; no source rows are dropped.
