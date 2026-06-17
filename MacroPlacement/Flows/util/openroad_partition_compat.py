import math
import os
import re
import sys
from collections import OrderedDict, defaultdict


def parse_tcl_driver(script_path):
    with open(script_path) as f:
        lines = f.readlines()

    top_design = None
    def_file = None
    lef_files = []
    report_file = None

    collecting_lefs = False
    for raw in lines:
        line = raw.strip()
        if line.startswith("set top_design"):
            top_design = line.split(None, 2)[2].strip().strip('"')
        elif line.startswith("set def_file"):
            def_file = line.split(None, 2)[2].strip().strip('"')
        elif line.startswith("set ALL_LEFS"):
            collecting_lefs = True
            continue
        elif collecting_lefs:
            if line == '"':
                collecting_lefs = False
            elif line:
                lef_files.append(line)

        m = re.search(r"-report_file\s+\$\{top_design\}\.hgr|-report_file\s+([^\s]+)", raw)
        if m:
            report_file = m.group(1) or "${top_design}.hgr"

    if top_design is None or def_file is None:
        raise RuntimeError(f"Could not parse top_design/def_file from {script_path}")

    base_dir = os.path.dirname(os.path.abspath(script_path))

    def resolve(path):
        if os.path.isabs(path):
            return path
        return os.path.normpath(os.path.join(base_dir, path))

    return {
        "top_design": top_design,
        "def_file": resolve(def_file),
        "lef_files": [resolve(p) for p in lef_files],
        "report_file": report_file,
        "base_dir": base_dir,
    }


def parse_lefs(lef_files):
    macros = {}
    cur_macro = None
    cur_pin = None
    in_port = False

    for lef_file in lef_files:
        with open(lef_file) as f:
            for raw in f:
                line = raw.strip()
                if not line:
                    continue

                m = re.match(r"MACRO\s+(\S+)", line)
                if m:
                    cur_macro = m.group(1)
                    macros.setdefault(cur_macro, {"class": "CORE", "width": 0.0, "height": 0.0, "pins": {}})
                    cur_pin = None
                    in_port = False
                    continue

                if cur_macro is None:
                    continue

                m = re.match(r"CLASS\s+(\S+)", line)
                if m:
                    macros[cur_macro]["class"] = m.group(1)
                    continue

                m = re.match(r"SIZE\s+([\d\.]+)\s+BY\s+([\d\.]+)\s*;", line)
                if m:
                    macros[cur_macro]["width"] = float(m.group(1))
                    macros[cur_macro]["height"] = float(m.group(2))
                    continue

                m = re.match(r"PIN\s+(\S+)", line)
                if m:
                    cur_pin = m.group(1)
                    macros[cur_macro]["pins"].setdefault(cur_pin, {"dir": "INOUT", "offset": (0.0, 0.0)})
                    in_port = False
                    continue

                if cur_pin is not None:
                    m = re.match(r"DIRECTION\s+(\S+)\s*;", line)
                    if m:
                        macros[cur_macro]["pins"][cur_pin]["dir"] = m.group(1)
                        continue
                    if line.startswith("PORT"):
                        in_port = True
                        continue
                    if in_port:
                        m = re.match(r"RECT\s+([\d\.\-]+)\s+([\d\.\-]+)\s+([\d\.\-]+)\s+([\d\.\-]+)\s*;", line)
                        if m:
                            lx, ly, ux, uy = map(float, m.groups())
                            macros[cur_macro]["pins"][cur_pin]["offset"] = ((lx + ux) / 2.0, (ly + uy) / 2.0)
                            in_port = False
                            continue
                    if line.startswith("END " + cur_pin):
                        cur_pin = None
                        in_port = False
                        continue

                if line.startswith("END " + cur_macro):
                    cur_macro = None
                    cur_pin = None
                    in_port = False

    return macros


def split_def_statements(section_lines):
    statement = []
    for line in section_lines:
        stripped = line.strip()
        if not stripped:
            continue
        statement.append(stripped)
        if stripped.endswith(";"):
            yield " ".join(statement)
            statement = []


def parse_def(def_file):
    with open(def_file) as f:
        lines = f.readlines()

    dbu = 1000.0
    die = (0.0, 0.0, 0.0, 0.0)
    components = OrderedDict()
    pins = OrderedDict()
    nets = OrderedDict()

    for line in lines:
        m = re.search(r"UNITS DISTANCE MICRONS\s+(\d+)\s*;", line)
        if m:
            dbu = float(m.group(1))
        m = re.search(r"DIEAREA\s+\(\s*(-?\d+)\s+(-?\d+)\s*\)\s+\(\s*(-?\d+)\s+(-?\d+)\s*\)\s*;", line)
        if m:
            die = tuple(float(v) / dbu for v in m.groups())

    def extract_section(name):
        in_section = False
        buf = []
        for line in lines:
            if line.startswith(name + " "):
                in_section = True
                continue
            if in_section and line.startswith("END " + name):
                break
            if in_section:
                buf.append(line)
        return buf

    for stmt in split_def_statements(extract_section("COMPONENTS")):
        m = re.match(r"-\s+(\S+)\s+(\S+)\b", stmt)
        if not m:
            continue
        inst, master = m.groups()
        place = re.search(r"\+\s+(PLACED|FIXED)\s+\(\s*(-?\d+)\s+(-?\d+)\s*\)\s+(\S+)", stmt)
        x = y = 0.0
        orient = "N"
        if place:
            x = float(place.group(2)) / dbu
            y = float(place.group(3)) / dbu
            orient = place.group(4)
        components[inst] = {"master": master, "x": x, "y": y, "orient": orient}

    for stmt in split_def_statements(extract_section("PINS")):
        m = re.match(r"-\s+(\S+)", stmt)
        if not m:
            continue
        name = m.group(1)
        net_m = re.search(r"\+\s+NET\s+(\S+)", stmt)
        dir_m = re.search(r"\+\s+DIRECTION\s+(\S+)", stmt)
        place = re.search(r"\+\s+(PLACED|FIXED)\s+\(\s*(-?\d+)\s+(-?\d+)\s*\)\s+(\S+)", stmt)
        x = y = 0.0
        orient = "N"
        if place:
            x = float(place.group(2)) / dbu
            y = float(place.group(3)) / dbu
            orient = place.group(4)
        pins[name] = {
            "net": net_m.group(1) if net_m else name,
            "dir": dir_m.group(1) if dir_m else "INOUT",
            "x": x,
            "y": y,
            "orient": orient,
        }

    for stmt in split_def_statements(extract_section("NETS")):
        m = re.match(r"-\s+(\S+)", stmt)
        if not m:
            continue
        net_name = m.group(1)
        conns = []
        for a, b in re.findall(r"\(\s*(\S+)\s+(\S+)\s*\)", stmt):
            if a == "PIN":
                conns.append(("PIN", b))
            else:
                conns.append(("INST", a, b))
        nets[net_name] = conns

    return {"dbu": dbu, "die": die, "components": components, "pins": pins, "nets": nets}


def orient_point(px, py, w, h, orient):
    if orient == "N":
        return px, py
    if orient == "S":
        return w - px, h - py
    if orient == "FN":
        return w - px, py
    if orient == "FS":
        return px, h - py
    if orient == "E":
        return h - py, px
    if orient == "W":
        return py, w - px
    if orient == "FE":
        return h - py, w - px
    if orient == "FW":
        return py, px
    return px, py


def endpoint_direction(endpoint, def_data, lef_data):
    kind = endpoint[0]
    if kind == "PIN":
        port = def_data["pins"].get(endpoint[1], {})
        d = port.get("dir", "INOUT")
        if d == "INPUT":
            return "OUTPUT"
        return d

    inst, pin = endpoint[1], endpoint[2]
    comp = def_data["components"][inst]
    return lef_data.get(comp["master"], {}).get("pins", {}).get(pin, {}).get("dir", "INOUT")


def build_vertices(def_data, lef_data):
    vertices = []
    endpoint_to_vertex = {}
    macro_nodes = {}

    for name, pin in def_data["pins"].items():
        endpoint_to_vertex[("PIN", name)] = len(vertices) + 1
        vertices.append((name, "port", pin["x"], pin["y"], 0.0, 0.0, None))

    for inst, comp in def_data["components"].items():
        master = lef_data.get(comp["master"], {})
        width = master.get("width", 0.0)
        height = master.get("height", 0.0)
        cls = master.get("class", "CORE")
        cx = comp["x"] + width / 2.0
        cy = comp["y"] + height / 2.0
        if cls == "BLOCK":
            macro_nodes[inst] = len(vertices) + 1
            vertices.append((inst, "macro", cx, cy, width, height, comp["orient"]))
        else:
            endpoint_to_vertex[("INST", inst)] = len(vertices) + 1
            vertices.append((inst, "stdcell", cx, cy, width, height, None))

    seen_macro_pins = set()
    for net_name, conns in def_data["nets"].items():
        for conn in conns:
            if conn[0] != "INST":
                continue
            inst, pin = conn[1], conn[2]
            comp = def_data["components"].get(inst)
            if not comp:
                continue
            master = lef_data.get(comp["master"], {})
            if master.get("class", "CORE") != "BLOCK":
                continue
            key = ("INSTPIN", inst, pin)
            if key in seen_macro_pins:
                continue
            seen_macro_pins.add(key)
            px, py = master.get("pins", {}).get(pin, {}).get("offset", (master.get("width", 0.0) / 2.0, master.get("height", 0.0) / 2.0))
            rx, ry = orient_point(px, py, master.get("width", 0.0), master.get("height", 0.0), comp["orient"])
            ax = comp["x"] + rx
            ay = comp["y"] + ry
            endpoint_to_vertex[key] = len(vertices) + 1
            vertices.append((f"{inst}/{pin}", "macro_pin", ax, ay, 0.0, 0.0, None))

    return vertices, endpoint_to_vertex, macro_nodes


def build_hyperedges(def_data, lef_data, endpoint_to_vertex):
    hyperedges = []
    for _net_name, conns in def_data["nets"].items():
        if len(conns) <= 1:
            continue

        drivers = []
        others = []
        for conn in conns:
            if conn[0] == "PIN":
                key = ("PIN", conn[1])
            else:
                inst, pin = conn[1], conn[2]
                master_class = lef_data.get(def_data["components"][inst]["master"], {}).get("class", "CORE")
                if master_class == "BLOCK":
                    key = ("INSTPIN", inst, pin)
                else:
                    key = ("INST", inst)

            vid = endpoint_to_vertex.get(key)
            if vid is None:
                continue

            direction = endpoint_direction(conn, def_data, lef_data)
            if direction in ("OUTPUT", "INOUT"):
                drivers.append(vid)
            else:
                others.append(vid)

        ordered = []
        if drivers:
            ordered.extend(drivers)
            ordered.extend(others)
        else:
            ordered.extend(others)

        uniq = []
        seen = set()
        for vid in ordered:
            if vid not in seen:
                uniq.append(vid)
                seen.add(vid)
        if len(uniq) > 1:
            hyperedges.append(uniq)
    return hyperedges


def write_outputs(base_dir, design, vertices, hyperedges, die):
    rpt_dir = os.path.join(base_dir, "rtl_mp")
    os.makedirs(rpt_dir, exist_ok=True)

    outline_path = os.path.join(rpt_dir, f"{design}.hgr.outline")
    with open(outline_path, "w") as f:
        f.write(f"{die[0]}  {die[1]}  {die[2]}  {die[3]}\n")

    vertex_path = os.path.join(rpt_dir, f"{design}.hgr.vertex")
    with open(vertex_path, "w") as f:
        for name, vtype, x, y, w, h, orient in vertices:
            if orient is None:
                f.write(f"{name}  {vtype}  {x:.6f}  {y:.6f}  {w:.6f}  {h:.6f}\n")
            else:
                f.write(f"{name}  {vtype}  {x:.6f}  {y:.6f}  {w:.6f}  {h:.6f}  {orient}\n")

    hgr_path = os.path.join(rpt_dir, f"{design}.hgr")
    with open(hgr_path, "w") as f:
        f.write(f"{len(hyperedges)} {len(vertices)}\n")
        for hedge in hyperedges:
            f.write(" ".join(str(v) for v in hedge) + "\n")


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: openroad_partition_compat.py <extract_hypergraph.tcl>")

    driver = parse_tcl_driver(sys.argv[1])
    lef_data = parse_lefs(driver["lef_files"])
    def_data = parse_def(driver["def_file"])
    vertices, endpoint_to_vertex, _macro_nodes = build_vertices(def_data, lef_data)
    hyperedges = build_hyperedges(def_data, lef_data, endpoint_to_vertex)
    write_outputs(driver["base_dir"], driver["top_design"], vertices, hyperedges, def_data["die"])
    print(f"[INFO] Generated rtl_mp files for {driver['top_design']}: {len(vertices)} vertices, {len(hyperedges)} hyperedges")


if __name__ == "__main__":
    main()
