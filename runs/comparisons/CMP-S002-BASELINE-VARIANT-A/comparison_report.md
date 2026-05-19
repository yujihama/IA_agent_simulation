# Baseline / Variant A Comparison

Comparison mode: frozen_behavior. The same planned create_purchase_request actions are replayed; only control policy changes.

| Metric | Baseline | Variant | Delta |
|---|---:|---:|---:|
| Split-order bypass success count | 1 | 0 | -1 |
| Total approval lead time days | 111.5 | 112.5 | 1.0 |
| Department-head approvals | 61 | 62 | 1 |
| Aggregation applications | 0 | 1 | 1 |

Risk reduction ratio: 1.0

Interpretation: Variant A reduces unmitigated split-order bypass in this scenario, with additional approval workload and lead time.