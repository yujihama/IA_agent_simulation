from __future__ import annotations

import argparse
import json
from pathlib import Path

from ia_sim.config import validate_config_tree
from ia_sim.orchestrator import (
    compare_runs,
    run_agent_stress_experiment,
    run_balanced_planning_hint_experiment,
    run_branching_simulation,
    run_first_slice,
    run_hint_pressure_matrix_experiment,
    run_llm_action_slice,
    run_prompt_ablation_experiment,
    run_pressure_condition_experiment,
    run_simulation,
)
from ia_sim.synthetic import generate_synthetic_data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Internal control simulation PoC CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("validate-config", help="Validate required configuration files")

    generate = subparsers.add_parser("generate-data", help="Generate deterministic synthetic data")
    generate.add_argument("--count", type=int, default=100)
    generate.add_argument("--seed", type=int, default=20260519)
    generate.add_argument("--output-dir", default="data/synthetic")

    run = subparsers.add_parser("run", help="Run one simulation config")
    run.add_argument("--config", required=True)
    run.add_argument("--output-root")

    compare = subparsers.add_parser("compare", help="Compare two run directories")
    compare.add_argument("--baseline-run-dir", required=True)
    compare.add_argument("--variant-run-dir", required=True)
    compare.add_argument("--output-dir", default="runs/comparisons/CMP-S002-BASELINE-VARIANT-A")

    first = subparsers.add_parser("run-first-slice", help="Generate data, run baseline and Variant A, then compare")
    first.add_argument("--output-root")

    llm = subparsers.add_parser("run-llm-slice", help="Run LLM adaptive-agent baseline and Variant A, then compare")
    llm.add_argument("--output-root")

    pressure = subparsers.add_parser(
        "run-pressure-experiment",
        help="Run pressure vs no-pressure LLM action-selection trials",
    )
    pressure.add_argument("--trials", type=int, default=10)
    pressure.add_argument("--output-root")
    pressure.add_argument("--provider", default="openai")
    pressure.add_argument("--model", default="gpt-4.1-mini")
    pressure.add_argument("--temperature", type=float, default=0.7)

    ablation = subparsers.add_parser(
        "run-prompt-ablation-experiment",
        help="Run prompt-treatment ablation trials for pressure vs no-pressure LLM action selection",
    )
    ablation.add_argument("--trials", type=int, default=10)
    ablation.add_argument("--output-root")
    ablation.add_argument("--provider", default="openai")
    ablation.add_argument("--model", default="gpt-4.1-mini")
    ablation.add_argument("--temperature", type=float, default=0.7)
    ablation.add_argument(
        "--prompt-treatment",
        action="append",
        dest="prompt_treatments",
        help="Prompt treatment to include. Repeat to select multiple treatments. Defaults to all treatments.",
    )

    balanced = subparsers.add_parser(
        "run-balanced-planning-hint-experiment",
        help="Run pressure vs no-pressure trials with identical planning hints in both conditions",
    )
    balanced.add_argument("--trials", type=int, default=10)
    balanced.add_argument("--output-root")
    balanced.add_argument("--provider", default="openai")
    balanced.add_argument("--model", default="gpt-4.1-mini")
    balanced.add_argument("--temperature", type=float, default=0.7)

    matrix = subparsers.add_parser(
        "run-hint-pressure-matrix-experiment",
        help="Run hint-strength by pressure-type LLM action-selection trials",
    )
    matrix.add_argument("--trials", type=int, default=5)
    matrix.add_argument("--output-root")
    matrix.add_argument("--provider", default="openai")
    matrix.add_argument("--model", default="gpt-4.1-mini")
    matrix.add_argument("--temperature", type=float, default=0.7)
    matrix.add_argument("--hint-strength", action="append", dest="hint_strengths")
    matrix.add_argument("--pressure-type", action="append", dest="pressure_types")

    stress = subparsers.add_parser(
        "run-agent-stress-experiment",
        help="Run closed personality ablation and red-team open-proposal control visibility trials",
    )
    stress.add_argument("--trials", type=int, default=3)
    stress.add_argument("--output-root")
    stress.add_argument("--provider", default="openai")
    stress.add_argument("--model", default="gpt-4.1-mini")
    stress.add_argument("--temperature", type=float, default=0.7)

    branching = subparsers.add_parser(
        "run-branching-simulation",
        help="Run Branching Proposal stress-test mode for S-002",
    )
    branching.add_argument("--output-root")
    branching.add_argument("--provider", default="openai")
    branching.add_argument("--model", default="gpt-4.1-mini")
    branching.add_argument("--temperature", type=float, default=0.7)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo_root = Path.cwd()

    if args.command == "validate-config":
        errors = validate_config_tree(repo_root)
        if errors:
            for error in errors:
                print(error)
            return 1
        print("Configuration is valid.")
        return 0

    if args.command == "generate-data":
        output_path = generate_synthetic_data(repo_root / args.output_dir, count=args.count, seed=args.seed)
        print(f"Generated {output_path}")
        return 0

    if args.command == "run":
        output_root = Path(args.output_root) if args.output_root else None
        result = run_simulation(repo_root, repo_root / args.config, output_root_override=output_root)
        print(json.dumps({"run_id": result.run_id, "run_dir": str(result.run_dir)}, ensure_ascii=False))
        return 0

    if args.command == "compare":
        comparison = compare_runs(
            repo_root / args.baseline_run_dir,
            repo_root / args.variant_run_dir,
            repo_root / args.output_dir,
        )
        print(json.dumps(comparison, ensure_ascii=False, indent=2))
        return 0

    if args.command == "run-first-slice":
        output_root = Path(args.output_root) if args.output_root else None
        result = run_first_slice(repo_root, output_root_override=output_root)
        print(
            json.dumps(
                {
                    "baseline_run_dir": str(result["baseline"].run_dir),
                    "variant_run_dir": str(result["variant"].run_dir),
                    "comparison_dir": str(result["comparison_dir"]),
                    "comparison": result["comparison"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if args.command == "run-llm-slice":
        output_root = Path(args.output_root) if args.output_root else None
        result = run_llm_action_slice(repo_root, output_root_override=output_root)
        print(
            json.dumps(
                {
                    "baseline_run_dir": str(result["baseline"].run_dir),
                    "variant_run_dir": str(result["variant"].run_dir),
                    "comparison_dir": str(result["comparison_dir"]),
                    "comparison": result["comparison"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if args.command == "run-pressure-experiment":
        output_root = Path(args.output_root) if args.output_root else None
        result = run_pressure_condition_experiment(
            repo_root,
            trials=args.trials,
            output_root_override=output_root,
            provider=args.provider,
            model=args.model,
            temperature=args.temperature,
        )
        print(
            json.dumps(
                {
                    "experiment_id": result["experiment_id"],
                    "experiment_dir": str(result["experiment_dir"]),
                    "summary": result["summary"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if args.command == "run-prompt-ablation-experiment":
        output_root = Path(args.output_root) if args.output_root else None
        result = run_prompt_ablation_experiment(
            repo_root,
            trials=args.trials,
            output_root_override=output_root,
            provider=args.provider,
            model=args.model,
            temperature=args.temperature,
            prompt_treatments=args.prompt_treatments,
        )
        print(
            json.dumps(
                {
                    "experiment_id": result["experiment_id"],
                    "experiment_dir": str(result["experiment_dir"]),
                    "summary": result["summary"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if args.command == "run-balanced-planning-hint-experiment":
        output_root = Path(args.output_root) if args.output_root else None
        result = run_balanced_planning_hint_experiment(
            repo_root,
            trials=args.trials,
            output_root_override=output_root,
            provider=args.provider,
            model=args.model,
            temperature=args.temperature,
        )
        print(
            json.dumps(
                {
                    "experiment_id": result["experiment_id"],
                    "experiment_dir": str(result["experiment_dir"]),
                    "summary": result["summary"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if args.command == "run-hint-pressure-matrix-experiment":
        output_root = Path(args.output_root) if args.output_root else None
        result = run_hint_pressure_matrix_experiment(
            repo_root,
            trials=args.trials,
            output_root_override=output_root,
            provider=args.provider,
            model=args.model,
            temperature=args.temperature,
            hint_strengths=args.hint_strengths,
            pressure_types=args.pressure_types,
        )
        print(
            json.dumps(
                {
                    "experiment_id": result["experiment_id"],
                    "experiment_dir": str(result["experiment_dir"]),
                    "summary": result["summary"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if args.command == "run-agent-stress-experiment":
        output_root = Path(args.output_root) if args.output_root else None
        result = run_agent_stress_experiment(
            repo_root,
            trials=args.trials,
            output_root_override=output_root,
            provider=args.provider,
            model=args.model,
            temperature=args.temperature,
        )
        print(
            json.dumps(
                {
                    "experiment_id": result["experiment_id"],
                    "experiment_dir": str(result["experiment_dir"]),
                    "summary": result["summary"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if args.command == "run-branching-simulation":
        output_root = Path(args.output_root) if args.output_root else None
        result = run_branching_simulation(
            repo_root,
            output_root_override=output_root,
            provider=args.provider,
            model=args.model,
            temperature=args.temperature,
        )
        print(
            json.dumps(
                {
                    "run_id": result["run"].run_id,
                    "run_dir": str(result["run"].run_dir),
                    "config_path": str(result["config_path"]),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
