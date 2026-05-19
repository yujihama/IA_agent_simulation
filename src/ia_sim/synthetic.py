from __future__ import annotations

import csv
from datetime import date, timedelta
from pathlib import Path

from ia_sim.models import PurchaseNeed


PURCHASE_NEED_FIELDS = [
    "purchase_need_id",
    "request_date",
    "requester_user_id",
    "department_id",
    "vendor_id",
    "project_id",
    "item_description",
    "amount_total",
    "needed_by",
    "scenario_id",
]


def build_purchase_needs(count: int = 100, seed: int = 20260519) -> list[PurchaseNeed]:
    if count < 1:
        raise ValueError("count must be at least 1")

    needs = [
        PurchaseNeed(
            purchase_need_id="NEED-001",
            request_date=date(2026, 6, 25),
            requester_user_id="USER-REQ-001",
            department_id="DEPT-SALES",
            vendor_id="VENDOR-014",
            project_id="PRJ-2026-Q2-017",
            item_description="Quarter-end analytics service package",
            amount_total=1_750_000,
            needed_by=date(2026, 6, 30),
            scenario_id="S-002",
        )
    ]

    start_date = date(2026, 4, 1)
    seed_offset = seed % 89
    for index in range(2, count + 1):
        request_date = start_date + timedelta(days=((index * 3) + seed_offset) % 88)
        amount = 120_000 + (((index + seed_offset) * 73_000) % 2_250_000)
        needs.append(
            PurchaseNeed(
                purchase_need_id=f"NEED-{index:03d}",
                request_date=request_date,
                requester_user_id=f"USER-REQ-{((index - 1) % 5) + 1:03d}",
                department_id=["DEPT-SALES", "DEPT-OPS", "DEPT-IT", "DEPT-FIN", "DEPT-HR"][
                    (index - 1) % 5
                ],
                vendor_id=f"VENDOR-{((index + 2) % 20) + 1:03d}",
                project_id=f"PRJ-2026-Q2-{index:03d}",
                item_description=f"Routine purchase package {index:03d}",
                amount_total=amount,
                needed_by=request_date + timedelta(days=14 + (index % 7)),
                scenario_id="S-002",
            )
        )
    return needs


def write_purchase_needs_csv(path: Path, needs: list[PurchaseNeed]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PURCHASE_NEED_FIELDS)
        writer.writeheader()
        for need in needs:
            writer.writerow(
                {
                    "purchase_need_id": need.purchase_need_id,
                    "request_date": need.request_date.isoformat(),
                    "requester_user_id": need.requester_user_id,
                    "department_id": need.department_id,
                    "vendor_id": need.vendor_id,
                    "project_id": need.project_id,
                    "item_description": need.item_description,
                    "amount_total": need.amount_total,
                    "needed_by": need.needed_by.isoformat(),
                    "scenario_id": need.scenario_id,
                }
            )


def read_purchase_needs_csv(path: Path) -> list[PurchaseNeed]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [
            PurchaseNeed(
                purchase_need_id=row["purchase_need_id"],
                request_date=date.fromisoformat(row["request_date"]),
                requester_user_id=row["requester_user_id"],
                department_id=row["department_id"],
                vendor_id=row["vendor_id"],
                project_id=row["project_id"],
                item_description=row["item_description"],
                amount_total=int(row["amount_total"]),
                needed_by=date.fromisoformat(row["needed_by"]),
                scenario_id=row["scenario_id"],
            )
            for row in reader
        ]


def generate_synthetic_data(output_dir: Path, count: int = 100, seed: int = 20260519) -> Path:
    needs = build_purchase_needs(count=count, seed=seed)
    output_path = output_dir / "purchase_needs.csv"
    write_purchase_needs_csv(output_path, needs)
    return output_path
