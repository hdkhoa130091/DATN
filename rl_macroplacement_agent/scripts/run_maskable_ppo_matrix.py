#!/usr/bin/env python3
"""Run repeated MaskablePPO experiments and summarize them for reporting."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import subprocess
import sys
import time
from pathlib import Path


def parse_int_list(raw: str) -> list[int]:
    values = [int(item.strip()) for item in raw.split(",") if item.strip()]
    if not values:
        raise argparse.ArgumentTypeError("expected at least one integer")
    return values


def run_command(command: list[str]) -> None:
    subprocess.run(command, check=True)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def aggregate(rows: list[dict]) -> list[dict]:
    grouped: dict[tuple[int, int], list[dict]] = {}
    for row in rows:
        grouped.setdefault((row["steps"], row["max_macros"]), []).append(row)

    summary_rows = []
    for (steps, max_macros), items in sorted(grouped.items()):
        best_costs = [float(item["best_cost"]) for item in items]
        final_costs = [float(item["eval_cost"]) for item in items]
        train_times = [
            float(item["train_runtime_sec"])
            for item in items
            if item["train_runtime_sec"] is not None
        ]
        eval_times = [float(item["eval_runtime_sec"]) for item in items]
        summary_rows.append(
            {
                "steps": steps,
                "max_macros": max_macros,
                "runs": len(items),
                "best_cost_mean": statistics.fmean(best_costs),
                "best_cost_std": statistics.pstdev(best_costs) if len(items) > 1 else 0.0,
                "best_cost_min": min(best_costs),
                "eval_cost_mean": statistics.fmean(final_costs),
                "eval_cost_std": statistics.pstdev(final_costs) if len(items) > 1 else 0.0,
                "train_runtime_mean_sec": statistics.fmean(train_times) if train_times else None,
                "eval_runtime_mean_sec": statistics.fmean(eval_times),
            }
        )
    return summary_rows


def render_markdown(rows: list[dict]) -> str:
    lines = [
        "| steps | macros | runs | best cost mean ± std | best cost min | eval cost mean ± std | train runtime mean (s) |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {steps} | {max_macros} | {runs} | {best_cost_mean:.6f} ± {best_cost_std:.6f} | "
            "{best_cost_min:.6f} | {eval_cost_mean:.6f} ± {eval_cost_std:.6f} | "
            "{train_runtime} |".format(
                **row,
                train_runtime=(
                    f"{row['train_runtime_mean_sec']:.2f}"
                    if row["train_runtime_mean_sec"] is not None
                    else "-"
                ),
            )
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run repeated MaskablePPO experiments.")
    parser.add_argument("--netlist", required=True)
    parser.add_argument("--init_plc", required=True)
    parser.add_argument("--out_dir", required=True)
    parser.add_argument("--steps", type=parse_int_list, default=parse_int_list("1000"))
    parser.add_argument("--max_macros", type=parse_int_list, default=parse_int_list("5,10,20"))
    parser.add_argument("--seeds", type=parse_int_list, default=parse_int_list("1,2,3"))
    parser.add_argument("--n_steps", type=int, default=128)
    parser.add_argument("--batch_size", type=int, default=64)
    parser.add_argument("--skip_existing", action="store_true")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    script_dir = Path(__file__).resolve().parent
    train_script = script_dir / "train_maskable_ppo.py"
    eval_script = script_dir / "evaluate_policy.py"

    raw_rows = []
    for steps in args.steps:
        for max_macros in args.max_macros:
            for seed in args.seeds:
                run_dir = out_dir / f"steps_{steps}" / f"macros_{max_macros}" / f"seed_{seed}"
                train_dir = run_dir / "train"
                eval_dir = run_dir / "eval"
                train_summary_path = train_dir / "train_summary.json"
                eval_summary_path = eval_dir / "ppo_eval_summary.json"

                if not (args.skip_existing and train_summary_path.exists()):
                    train_start = time.perf_counter()
                    run_command(
                        [
                            sys.executable,
                            str(train_script),
                            "--netlist",
                            args.netlist,
                            "--init_plc",
                            args.init_plc,
                            "--out_dir",
                            str(train_dir),
                            "--steps",
                            str(steps),
                            "--max_macros",
                            str(max_macros),
                            "--seed",
                            str(seed),
                            "--n_steps",
                            str(args.n_steps),
                            "--batch_size",
                            str(args.batch_size),
                        ]
                    )
                    train_runtime = time.perf_counter() - train_start
                else:
                    train_runtime = None

                train_summary = load_json(train_summary_path)
                if not (args.skip_existing and eval_summary_path.exists()):
                    eval_start = time.perf_counter()
                    run_command(
                        [
                            sys.executable,
                            str(eval_script),
                            "--model",
                            train_summary["model_path"],
                            "--netlist",
                            args.netlist,
                            "--init_plc",
                            args.init_plc,
                            "--out_dir",
                            str(eval_dir),
                            "--max_macros",
                            str(max_macros),
                            "--deterministic",
                        ]
                    )
                    eval_runtime_wall = time.perf_counter() - eval_start
                else:
                    eval_runtime_wall = None

                eval_summary = load_json(eval_summary_path)
                raw_rows.append(
                    {
                        "steps": steps,
                        "max_macros": max_macros,
                        "seed": seed,
                        "best_cost": train_summary["best_cost"],
                        "eval_cost": eval_summary["cost"],
                        "eval_best_cost": eval_summary["best_cost"],
                        "wirelength": eval_summary["wirelength"],
                        "density_cost": eval_summary["density_cost"],
                        "congestion_cost": eval_summary["congestion_cost"],
                        "train_runtime_sec": train_runtime,
                        "eval_runtime_sec": eval_summary["runtime_sec"],
                        "eval_wall_runtime_sec": eval_runtime_wall,
                        "run_dir": str(run_dir),
                    }
                )

    raw_fields = [
        "steps",
        "max_macros",
        "seed",
        "best_cost",
        "eval_cost",
        "eval_best_cost",
        "wirelength",
        "density_cost",
        "congestion_cost",
        "train_runtime_sec",
        "eval_runtime_sec",
        "eval_wall_runtime_sec",
        "run_dir",
    ]
    raw_path = out_dir / "matrix_runs.csv"
    write_csv(raw_path, raw_rows, raw_fields)
    (out_dir / "matrix_runs.json").write_text(json.dumps(raw_rows, indent=2), encoding="utf-8")

    summary_rows = aggregate(raw_rows)
    summary_fields = [
        "steps",
        "max_macros",
        "runs",
        "best_cost_mean",
        "best_cost_std",
        "best_cost_min",
        "eval_cost_mean",
        "eval_cost_std",
        "train_runtime_mean_sec",
        "eval_runtime_mean_sec",
    ]
    write_csv(out_dir / "matrix_summary.csv", summary_rows, summary_fields)
    (out_dir / "matrix_summary.json").write_text(
        json.dumps(summary_rows, indent=2), encoding="utf-8"
    )
    markdown = render_markdown(summary_rows)
    (out_dir / "matrix_summary.md").write_text(markdown, encoding="utf-8")
    print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
