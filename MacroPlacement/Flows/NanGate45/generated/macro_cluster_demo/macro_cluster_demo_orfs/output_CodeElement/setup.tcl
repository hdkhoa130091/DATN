set design "macro_cluster_demo"
set top_design "macro_cluster_demo"
set netlist "/workspace/DATN/MacroPlacement/Flows/NanGate45/generated/macro_cluster_demo/macro_cluster_demo_orfs/def/macro_cluster_demo.v"
set def_file "/workspace/DATN/MacroPlacement/Flows/NanGate45/generated/macro_cluster_demo/macro_cluster_demo_orfs/def/macro_cluster_demo.def"
set ALL_LEFS "
    ./lef/NangateOpenCellLibrary.tech.lef
    ./lef/fakeram45_256x16.lef
    ./lef/NangateOpenCellLibrary.macro.mod.lef
"
set LIB_BC "
    ./lib/fakeram45_256x16.lib
    ./lib/NangateOpenCellLibrary_typical.lib
"
set site "FreePDK45_38x28_10R_NP_162NW_34O"
foreach lef_file ${ALL_LEFS} {
    read_lef $lef_file
}
foreach lib_file ${LIB_BC} {
    read_liberty $lib_file
}