# coding=utf-8
# Copyright 2021 The Circuit Training Team Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""An example and simple binary to create and call plc client."""

import os
import shutil
import sys
from typing import Sequence

from absl import app
from absl import flags
from circuit_training.environment import plc_client

flags.DEFINE_string("netlist_file", None, "Path to the input netlist file.")

flags.mark_flags_as_required([
    "netlist_file",
])

FLAGS = flags.FLAGS


def _parse_plc_metadata(plc_path: str):
  cols = rows = None
  width = height = None
  with open(plc_path) as f:
    for line in f:
      items = line.split()
      if len(items) > 6 and items[0] == "#" and items[1] == "Columns":
        cols = int(items[3])
        rows = int(items[6])
      elif len(items) > 6 and items[0] == "#" and items[1] == "Width":
        width = float(items[3])
        height = float(items[6])
      if None not in (cols, rows, width, height):
        break
  return cols, rows, width, height


def _fallback_plc():
  macroplacement_codeelements = "/home/DATN/MacroPlacement/CodeElements"
  if macroplacement_codeelements not in sys.path:
    sys.path.insert(0, macroplacement_codeelements)
  from Plc_client import plc_client_os  # pylint: disable=import-error

  plc = plc_client_os.PlacementCost(netlist_file=FLAGS.netlist_file)
  plc_dir = os.path.dirname(FLAGS.netlist_file)
  plc_candidates = [
      os.path.join(plc_dir, "initial.plc"),
      os.path.join(plc_dir, "init.plc"),
  ]
  plc_path = next((p for p in plc_candidates if os.path.exists(p)), None)
  if plc_path:
    cols, rows, width, height = _parse_plc_metadata(plc_path)
    if None not in (cols, rows, width, height):
      plc.set_canvas_size(width, height)
      plc.set_placement_grid(cols, rows)
      plc.set_routes_per_micron(10.0, 10.0)
      plc.set_macro_routing_allocation(5.0, 5.0)
      plc.set_congestion_smooth_range(2)
      plc.set_canvas_boundary_check(False)
      plc.restore_placement(plc_path, ifInital=True, ifValidate=False, ifReadComment=False)
  return plc


def main(argv: Sequence[str]) -> None:
  if len(argv) > 1:
    raise app.UsageError("Too many command-line arguments.")

  if shutil.which("plc_wrapper_main"):
    plc = plc_client.PlacementCost(netlist_file=FLAGS.netlist_file)
  else:
    print("plc_wrapper_main not found. Falling back to MacroPlacement plc_client_os.")
    plc = _fallback_plc()

  print("get_cost:", plc.get_cost())
  print("get_congestion_cost:", plc.get_congestion_cost())
  print("get_density_cost:", plc.get_density_cost())

  hard_macro_indices = [
      m for m in plc.get_macro_indices() if not plc.is_node_soft_macro(m)
  ]
  print("hard_macro_indices:", hard_macro_indices)
  print("get_node_mask:", plc.get_node_mask(hard_macro_indices[0]))


if __name__ == "__main__":
  app.run(main)
