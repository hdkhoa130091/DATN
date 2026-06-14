# Copy this file into flow/designs/nangate45/<design>/config.mk.
export DESIGN_NAME = my_top
export DESIGN_NICKNAME = custom_template
export PLATFORM = nangate45

export VERILOG_FILES = $(DESIGN_HOME)/src/$(DESIGN_NICKNAME)/my_top.v
export SDC_FILE = $(DESIGN_HOME)/$(PLATFORM)/$(DESIGN_NICKNAME)/constraint.sdc

export CORE_UTILIZATION = 50
export CORE_ASPECT_RATIO = 1
export CORE_MARGIN = 5
export ABC_AREA = 1
