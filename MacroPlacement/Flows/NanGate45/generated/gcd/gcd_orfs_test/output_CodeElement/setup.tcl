set design "gcd"
set top_design "gcd"
set netlist "/home/khoahd/Documents/DATN-1/MacroPlacement/Flows/NanGate45/generated/gcd/gcd_orfs_test/def/gcd.v"
set def_file "/home/khoahd/Documents/DATN-1/MacroPlacement/Flows/NanGate45/generated/gcd/gcd_orfs_test/def/gcd.def"
set ALL_LEFS "
    ./lef/NangateOpenCellLibrary.macro.mod.lef
    ./lef/NangateOpenCellLibrary.tech.lef
"
set LIB_BC "
    ./lib/NangateOpenCellLibrary_typical.lib
"
set site "FreePDK45_38x28_10R_NP_162NW_34O"
foreach lef_file ${ALL_LEFS} {
    read_lef $lef_file
}
foreach lib_file ${LIB_BC} {
    read_liberty $lib_file
}