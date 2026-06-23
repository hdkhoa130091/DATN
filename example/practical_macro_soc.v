(* blackbox *)
module fakeram45_256x16 (
    input wire clk,
    output wire [15:0] rd_out,
    input wire ce_in,
    input wire we_in,
    input wire [7:0] addr_in,
    input wire [15:0] w_mask_in,
    input wire [15:0] wd_in
);
endmodule

module practical_macro_soc (
    input wire clk,
    input wire rst_n,
    input wire start,
    input wire irq_i,
    output wire [31:0] status_o
);
    reg [7:0] pc_q;
    reg [7:0] data_addr_q;
    reg [7:0] dma_addr_q;
    reg [7:0] io_addr_q;
    reg [15:0] seed_q;
    reg [2:0] phase_q;

    wire [15:0] instr0_rd;
    wire [15:0] instr1_rd;
    wire [15:0] data0_rd;
    wire [15:0] data1_rd;
    wire [15:0] dma0_rd;
    wire [15:0] dma1_rd;
    wire [15:0] io0_rd;
    wire [15:0] io1_rd;

    wire active = start | irq_i;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pc_q <= 8'h00;
            data_addr_q <= 8'h10;
            dma_addr_q <= 8'h20;
            io_addr_q <= 8'h30;
            seed_q <= 16'h1a2b;
            phase_q <= 3'd0;
        end else if (active) begin
            pc_q <= pc_q + 8'h01;
            data_addr_q <= data_addr_q + {5'd0, phase_q};
            dma_addr_q <= dma_addr_q + 8'h02;
            io_addr_q <= io_addr_q + 8'h03;
            seed_q <= seed_q ^ {instr0_rd[7:0], data1_rd[7:0]};
            phase_q <= phase_q + 3'd1;
        end
    end

    wire ce_instr0_b = ~(active & (phase_q[0] == 1'b0));
    wire ce_instr1_b = ~(active & (phase_q[0] == 1'b1));
    wire ce_data0_b = ~(active & (phase_q[1] == 1'b0));
    wire ce_data1_b = ~(active & (phase_q[1] == 1'b1));
    wire ce_dma0_b = ~(active & (phase_q[2] == 1'b0));
    wire ce_dma1_b = ~(active & (phase_q[2] == 1'b1));
    wire ce_io0_b = ~(active & irq_i);
    wire ce_io1_b = ~(active & ~irq_i);
    wire we_b = 1'b1;

    wire [15:0] wd_instr0 = seed_q ^ 16'h1111;
    wire [15:0] wd_instr1 = seed_q ^ 16'h2222;
    wire [15:0] wd_data0 = instr0_rd ^ dma0_rd;
    wire [15:0] wd_data1 = instr1_rd ^ dma1_rd;
    wire [15:0] wd_dma0 = data0_rd + io0_rd;
    wire [15:0] wd_dma1 = data1_rd + io1_rd;
    wire [15:0] wd_io0 = instr0_rd ^ data1_rd ^ 16'h00ff;
    wire [15:0] wd_io1 = instr1_rd ^ data0_rd ^ 16'hff00;

    fakeram45_256x16 u_instr_mem0 (
        .clk(clk),
        .rd_out(instr0_rd),
        .ce_in(ce_instr0_b),
        .we_in(we_b),
        .addr_in(pc_q),
        .w_mask_in(16'hffff),
        .wd_in(wd_instr0)
    );

    fakeram45_256x16 u_instr_mem1 (
        .clk(clk),
        .rd_out(instr1_rd),
        .ce_in(ce_instr1_b),
        .we_in(we_b),
        .addr_in(pc_q + 8'h04),
        .w_mask_in(16'hffff),
        .wd_in(wd_instr1)
    );

    fakeram45_256x16 u_data_mem0 (
        .clk(clk),
        .rd_out(data0_rd),
        .ce_in(ce_data0_b),
        .we_in(we_b),
        .addr_in(data_addr_q),
        .w_mask_in(16'hffff),
        .wd_in(wd_data0)
    );

    fakeram45_256x16 u_data_mem1 (
        .clk(clk),
        .rd_out(data1_rd),
        .ce_in(ce_data1_b),
        .we_in(we_b),
        .addr_in(data_addr_q + 8'h08),
        .w_mask_in(16'hffff),
        .wd_in(wd_data1)
    );

    fakeram45_256x16 u_dma_mem0 (
        .clk(clk),
        .rd_out(dma0_rd),
        .ce_in(ce_dma0_b),
        .we_in(we_b),
        .addr_in(dma_addr_q),
        .w_mask_in(16'hffff),
        .wd_in(wd_dma0)
    );

    fakeram45_256x16 u_dma_mem1 (
        .clk(clk),
        .rd_out(dma1_rd),
        .ce_in(ce_dma1_b),
        .we_in(we_b),
        .addr_in(dma_addr_q + 8'h10),
        .w_mask_in(16'hffff),
        .wd_in(wd_dma1)
    );

    fakeram45_256x16 u_io_mem0 (
        .clk(clk),
        .rd_out(io0_rd),
        .ce_in(ce_io0_b),
        .we_in(we_b),
        .addr_in(io_addr_q),
        .w_mask_in(16'hffff),
        .wd_in(wd_io0)
    );

    fakeram45_256x16 u_io_mem1 (
        .clk(clk),
        .rd_out(io1_rd),
        .ce_in(ce_io1_b),
        .we_in(we_b),
        .addr_in(io_addr_q + 8'h20),
        .w_mask_in(16'hffff),
        .wd_in(wd_io1)
    );

    wire [15:0] fabric_mix0 = instr0_rd ^ data0_rd ^ dma0_rd;
    wire [15:0] fabric_mix1 = instr1_rd ^ data1_rd ^ dma1_rd;
    wire [15:0] fabric_mix2 = io0_rd + io1_rd + seed_q;
    wire [15:0] fabric_mix3 = {8'h00, pc_q} ^ {8'h00, phase_q, 5'b0};

    assign status_o = {fabric_mix0 ^ fabric_mix2, fabric_mix1 ^ fabric_mix3};
endmodule
