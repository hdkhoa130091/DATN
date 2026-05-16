#!/usr/bin/env python3
"""Reusable speedups for the open-source PlacementCost implementation."""

from __future__ import annotations

from types import MethodType


def install_fast_wirelength_cache(evaluator) -> None:
    """Cache static pin-parent/net relations for repeated HPWL evaluation."""
    modules = evaluator.modules_w_pins
    name_to_idx = evaluator.mod_name_to_indices

    pin_refs: dict[int, tuple[int, float, float]] = {}
    for pin_idx in set(
        evaluator.port_indices
        + evaluator.soft_macro_pin_indices
        + evaluator.hard_macro_pin_indices
    ):
        pin = modules[pin_idx]
        if pin.get_type() == "PORT":
            pin_refs[pin_idx] = (pin_idx, 0.0, 0.0)
        else:
            ref_idx = name_to_idx[pin.get_macro_name()]
            off_x, off_y = pin.get_offset()
            pin_refs[pin_idx] = (ref_idx, off_x, off_y)

    net_terms = []
    for driver_name, sink_names in evaluator.nets.items():
        driver_idx = name_to_idx[driver_name]
        pin_indices = [driver_idx, *(name_to_idx[name] for name in sink_names)]
        net_terms.append((modules[driver_idx].get_weight(), tuple(pin_indices)))

    def fast_get_wirelength(plc) -> float:
        total_hpwl = 0.0
        modules_local = plc.modules_w_pins
        for weight, pin_indices in plc._fast_net_terms:
            ref_idx, off_x, off_y = plc._fast_pin_refs[pin_indices[0]]
            min_x = max_x = modules_local[ref_idx].get_pos()[0] + off_x
            min_y = max_y = modules_local[ref_idx].get_pos()[1] + off_y
            for pin_idx in pin_indices[1:]:
                ref_idx, off_x, off_y = plc._fast_pin_refs[pin_idx]
                ref_x, ref_y = modules_local[ref_idx].get_pos()
                x = ref_x + off_x
                y = ref_y + off_y
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)
            total_hpwl += weight * ((max_x - min_x) + (max_y - min_y))
        return total_hpwl

    evaluator._fast_pin_refs = pin_refs
    evaluator._fast_net_terms = tuple(net_terms)
    evaluator.get_wirelength = MethodType(fast_get_wirelength, evaluator)
