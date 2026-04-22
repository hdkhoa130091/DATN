#!/usr/bin/env python3
from pathlib import Path
import sys


def main() -> int:
    repo_root = Path("/home/DATN/OpenROAD-flow-scripts/flow/scripts")
    if not repo_root.exists():
        print(f"Missing ORFS scripts directory: {repo_root}", file=sys.stderr)
        return 1

    changed = []

    cts = repo_root / "cts.tcl"
    cts_text = cts.read_text()
    cts_original = cts_text
    cts_text = cts_text.replace(
        "set cts_args [list \\\n  -sink_clustering_enable \\\n  -repair_clock_nets]",
        "set cts_args [list \\\n  -sink_clustering_enable]",
    )
    cts_text = cts_text.replace(
        "log_cmd repair_clock_nets\nlog_cmd repair_clock_nets\n",
        "log_cmd repair_clock_nets\n",
    )
    if "log_cmd repair_clock_nets\n" not in cts_text:
        cts_text = cts_text.replace(
            "log_cmd clock_tree_synthesis {*}$cts_args\n",
            "log_cmd clock_tree_synthesis {*}$cts_args\nlog_cmd repair_clock_nets\n",
            1,
        )
    if cts_text != cts_original:
        cts.write_text(cts_text)
        changed.append(cts)

    floorplan = repo_root / "floorplan.tcl"
    floorplan_text = floorplan.read_text()
    floorplan_original = floorplan_text
    floorplan_text = floorplan_text.replace(
        '  repair_timing_helper -setup -skip_last_gasp -sequence "unbuffer,sizeup,swap,vt_swap"\n',
        "  repair_timing_helper -setup -skip_last_gasp\n",
    )
    floorplan_text = floorplan_text.replace(
        "report_units_metric\nreport_layer_rc\n",
        'if {[llength [info commands report_units_metric]]} {\n  report_units_metric\n}\nif {[llength [info commands report_layer_rc]]} {\n  report_layer_rc\n}\n',
    )
    if floorplan_text != floorplan_original:
        floorplan.write_text(floorplan_text)
        changed.append(floorplan)

    util = repo_root / "util.tcl"
    util_text = util.read_text()
    util_original = util_text
    util_text = util_text.replace(
        "  append_env_var additional_args SETUP_MOVE_SEQUENCE -sequence 1\n",
        "",
    )
    if util_text != util_original:
        util.write_text(util_text)
        changed.append(util)

    global_place_skip_io = repo_root / "global_place_skip_io.tcl"
    gp_skip_text = global_place_skip_io.read_text()
    gp_skip_original = gp_skip_text
    gp_skip_text = gp_skip_text.replace(
        "} elseif { [all_pins_placed] } {\n",
        "} elseif { [llength [info commands all_pins_placed]] && [all_pins_placed] } {\n",
    )
    if gp_skip_text != gp_skip_original:
        global_place_skip_io.write_text(gp_skip_text)
        changed.append(global_place_skip_io)

    global_place = repo_root / "global_place.tcl"
    global_place_text = global_place.read_text()
    global_place_original = global_place_text
    global_place_text = global_place_text.replace(
        "lappend global_placement_args -force_center_initial_place\n",
        "",
    )
    if global_place_text != global_place_original:
        global_place.write_text(global_place_text)
        changed.append(global_place)

    report_metrics = repo_root / "report_metrics.tcl"
    report_metrics_text = report_metrics.read_text()
    report_metrics_original = report_metrics_text
    report_metrics_text = report_metrics_text.replace(
        "  report_tns_metric\n",
        '  if {[llength [info commands report_tns_metric]]} {\n    report_tns_metric\n  }\n',
    )
    report_metrics_text = report_metrics_text.replace(
        "  report_tns_metric -hold\n",
        '  if {[llength [info commands report_tns_metric]]} {\n    report_tns_metric -hold\n  }\n',
    )
    report_metrics_text = report_metrics_text.replace(
        "  report_worst_slack_metric\n",
        '  if {[llength [info commands report_worst_slack_metric]]} {\n    report_worst_slack_metric\n  }\n',
    )
    report_metrics_text = report_metrics_text.replace(
        "  report_worst_slack_metric -hold\n",
        '  if {[llength [info commands report_worst_slack_metric]]} {\n    report_worst_slack_metric -hold\n  }\n',
    )
    report_metrics_text = report_metrics_text.replace(
        "  report_fmax_metric\n",
        '  if {[llength [info commands report_fmax_metric]]} {\n    report_fmax_metric\n  }\n',
    )
    report_metrics_text = report_metrics_text.replace(
        "    report_clock_skew_metric\n",
        '    if {[llength [info commands report_clock_skew_metric]]} {\n      report_clock_skew_metric\n    }\n',
    )
    report_metrics_text = report_metrics_text.replace(
        "    report_clock_skew_metric -hold\n",
        '    if {[llength [info commands report_clock_skew_metric]]} {\n      report_clock_skew_metric -hold\n    }\n',
    )
    report_metrics_text = report_metrics_text.replace(
        "    report_erc_metrics\n",
        '    if {[llength [info commands report_erc_metrics]]} {\n      report_erc_metrics\n    }\n',
    )
    report_metrics_text = report_metrics_text.replace(
        "      report_power_metric -corner $corner\n",
        '      if {[llength [info commands report_power_metric]]} {\n        report_power_metric -corner $corner\n      }\n',
    )
    report_metrics_text = report_metrics_text.replace(
        "    report_power_metric\n",
        '    if {[llength [info commands report_power_metric]]} {\n      report_power_metric\n    }\n',
    )
    report_metrics_text = report_metrics_text.replace(
        "  report_design_area_metrics\n",
        '  if {[llength [info commands report_design_area_metrics]]} {\n    report_design_area_metrics\n  }\n',
    )
    if report_metrics_text != report_metrics_original:
        report_metrics.write_text(report_metrics_text)
        changed.append(report_metrics)

    if changed:
        print("Patched files:")
        for path in changed:
            print(path)
    else:
        print("No changes needed.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
