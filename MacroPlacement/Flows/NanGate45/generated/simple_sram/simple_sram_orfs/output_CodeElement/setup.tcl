set design "simple_sram"
set top_design "simple_sram"
set netlist "/workspace/DATN/MacroPlacement/Flows/NanGate45/generated/simple_sram/simple_sram_orfs/def/simple_sram.v"
set def_file "/workspace/DATN/MacroPlacement/Flows/NanGate45/generated/simple_sram/simple_sram_orfs/def/simple_sram.def"
set ALL_LEFS "
    ./lef/NangateOpenCellLibrary.tech.lef
    ./lef/NangateOpenCellLibrary.macro.mod.lef
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