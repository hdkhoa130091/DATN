#!/usr/bin/env bash
set -e

mkdir -p logs

TMP_DIR="/tmp/yosys_adder_test"
mkdir -p "${TMP_DIR}"
cd "${TMP_DIR}"

cat > adder.v <<'EOF'
module adder(
    input  [3:0] a,
    input  [3:0] b,
    output [4:0] y
);
assign y = a + b;
endmodule
EOF

cat > synth.ys <<'EOF'
read_verilog adder.v
synth -top adder
abc
write_verilog netlist.v
EOF

{
  echo "=== yosys synth.ys ==="
  yosys synth.ys
  echo
  echo "=== head -80 netlist.v ==="
  head -80 netlist.v
} 2>&1 | tee /workspace/DATN/datn_docker_env/logs/yosys_test.log
