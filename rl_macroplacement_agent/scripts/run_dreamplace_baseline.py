#!/usr/bin/env python3
"""Run official DREAMPlace and optionally align its placement to .plc metrics."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path


def find_latest_pl(output_dir: Path) -> Path | None:
    candidates = sorted(output_dir.rglob("*.pl"), key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Run DREAMPlace baseline.")
    parser.add_argument("--dreamplace_root", default="DREAMPlace")
    parser.add_argument("--json", required=True, help="DREAMPlace benchmark JSON config")
    parser.add_argument("--out_dir", required=True)
    parser.add_argument("--netlist", help="MacroPlacement netlist.pb.txt for aligned evaluation")
    parser.add_argument("--template_plc", help="Initial .plc for aligned conversion")
    parser.add_argument("--converted_plc", help="Output converted .plc path")
    parser.add_argument("--python", default="python3")
    parser.add_argument("--skip_run", action="store_true", help="Only convert/evaluate existing output")
    parser.add_argument("--existing_pl", help="Existing DREAMPlace .pl to convert/evaluate")
    args = parser.parse_args()

    dreamplace_root = Path(args.dreamplace_root).resolve()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    runtime = None
    returncode = 0
    stdout_path = out_dir / "dreamplace_stdout.log"
    stderr_path = out_dir / "dreamplace_stderr.log"

    if not args.skip_run:
        placer = dreamplace_root / "dreamplace" / "Placer.py"
        if not placer.is_file():
            raise FileNotFoundError(f"DREAMPlace Placer.py not found: {placer}")
        command = [args.python, str(placer), args.json]
        start = time.perf_counter()
        proc = subprocess.run(
            command,
            cwd=str(dreamplace_root),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        runtime = time.perf_counter() - start
        returncode = proc.returncode
        stdout_path.write_text(proc.stdout, encoding="utf-8")
        stderr_path.write_text(proc.stderr, encoding="utf-8")
        if proc.returncode != 0:
            raise RuntimeError(f"DREAMPlace failed with return code {proc.returncode}; see {stderr_path}")

    pl_path = Path(args.existing_pl) if args.existing_pl else find_latest_pl(out_dir)
    converted_plc = None
    if pl_path and args.netlist and args.template_plc:
        converted_plc = Path(args.converted_plc) if args.converted_plc else out_dir / "dreamplace.plc"
        converter = Path(__file__).with_name("convert_bookshelf_pl_to_plc.py")
        subprocess.run(
            [
                args.python,
                str(converter),
                "--dreamplace_pl",
                str(pl_path),
                "--template_plc",
                args.template_plc,
                "--netlist",
                args.netlist,
                "--out",
                str(converted_plc),
            ],
            check=True,
        )

    summary = {
        "method": "DREAMPlace",
        "dreamplace_root": str(dreamplace_root),
        "config_json": args.json,
        "output_dir": str(out_dir),
        "runtime_sec": runtime,
        "returncode": returncode,
        "stdout_log": str(stdout_path),
        "stderr_log": str(stderr_path),
        "dreamplace_pl": str(pl_path) if pl_path else None,
        "converted_plc": str(converted_plc) if converted_plc else None,
    }
    summary_path = out_dir / "dreamplace_run_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
