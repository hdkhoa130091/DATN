# Replace clk with the actual clock port. Remove this line for combinational designs.
create_clock -name core_clock -period 10.0 [get_ports clk]
