# First Vertical Slice Implementation Notes

This note records implementation decisions for `S-002 x D-001 x Baseline / Variant A`.

## Action Space

Closed Action Mode exposes neutral actions only:

- `create_purchase_request`
- `consult_manager`
- `consult_purchasing`
- `postpone_request`

`submit_split_requests` is intentionally absent. Split-order suspicion is detected from multiple `create_purchase_request` events, not from an action name.

`select_request_route` is not used in this slice. Route selection is represented by the `route_type` field on `create_purchase_request`.

## PurchaseNeed.status

- `open`: no purchase request exists.
- `partially_requested`: at least one purchase request exists and the requested amount is below the purchase need total.
- `requested`: the requested amount is equal to or above the purchase need total.
- `postponed`: the requester selected `postpone_request`.

## Detector Outputs

Each run writes `detector_annotations.jsonl`. The `split_order_detector` annotates candidate event groups and records observed facts, inference, related controls, evidence event IDs, and whether the sequence was mitigated by aggregation.

`proposal_flags` from Open Proposal Mode are not used for detector performance metrics. This first slice sets `proposal_flags_used: false` and computes precision/recall only from event-based detector annotations and ground truth labels.

Raw events, detector annotations, and findings do not include `evaluation_group_id`, `behavior_pattern`, or `evaluation_result`. Ground truth matching is written only to `evaluation_results.json`, using observable event keys such as `purchase_need_id`.

## Frozen Behavior

Each run writes `behavior_replay_log.jsonl`. Baseline and Variant A use the same planned neutral action sequence, so the comparison isolates the control-policy change:

- Baseline evaluates each request independently.
- Variant A aggregates requests by requester, vendor, and project within 7 days.

## Scope Stubs

In this First Slice, approval actors and SOD checks are still stubs. The repository includes `user_master.yaml`, `approval_matrix.yaml`, and `sod_policies.yaml` as schema/data foundations, but the simulation currently uses a small in-code approver directory and a requester-versus-approver SOD check. A next slice should load approval levels and SOD incompatibilities from these masters.

## Reproducibility

`seed` is passed into synthetic data generation. The embedded D-001 scenario remains fixed for `NEED-001`, while routine synthetic purchases vary deterministically by seed.

`max_purchase_needs` counts purchase needs, not purchase requests. With the S-002 first-slice fixture, 100 purchase needs produce 101 purchase requests because `NEED-001` is represented by two neutral `create_purchase_request` actions.

## Committed Evidence

The First Vertical Slice fixture and outputs are committed as PoC evidence:

- `data/synthetic/purchase_needs.csv`
- `runs/RUN-S002-BASELINE/`
- `runs/RUN-S002-VARIANT-A/`
- `runs/comparisons/CMP-S002-BASELINE-VARIANT-A/`

`purchase_needs.csv` is a fixed synthetic input fixture for `RUN-S002-BASELINE` and `RUN-S002-VARIANT-A`. It does not contain Ground Truth labels. Ground Truth remains isolated in `data/synthetic/ground_truth_labels.yaml`.

The committed run manifests use repository-relative paths and include `seed`, `code_version`, `config_hashes`, and `data_hashes`. Real data, anonymized production logs, and confidential run outputs should not be committed.
