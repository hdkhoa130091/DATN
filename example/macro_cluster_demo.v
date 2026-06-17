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

module macro_cluster_demo (
    input wire clk,
    input wire rst_n,
    input wire start,
    output wire [15:0] gpio_out
);
    reg [7:0] addr_q;
    reg [15:0] data_q;
    reg [1:0] bank_sel_q;

    wire [15:0] rd0;
    wire [15:0] rd1;
    wire [15:0] rd2;
    wire [15:0] rd3;

    wire ce0_b = ~(start & (bank_sel_q == 2'd0));
    wire ce1_b = ~(start & (bank_sel_q == 2'd1));
    wire ce2_b = ~(start & (bank_sel_q == 2'd2));
    wire ce3_b = ~(start & (bank_sel_q == 2'd3));
    wire we_b = 1'b1;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            addr_q <= 8'h00;
            data_q <= 16'h1234;
            bank_sel_q <= 2'd0;
        end else if (start) begin
            addr_q <= addr_q + 8'h01;
            data_q <= data_q + 16'h0101;
            bank_sel_q <= bank_sel_q + 2'd1;
        end
    end

    fakeram45_256x16 u_mem0 (
        .clk(clk),
        .rd_out(rd0),
        .ce_in(ce0_b),
        .we_in(we_b),
        .addr_in(addr_q),
        .w_mask_in(16'hffff),
        .wd_in(data_q)
    );

    fakeram45_256x16 u_mem1 (
        .clk(clk),
        .rd_out(rd1),
        .ce_in(ce1_b),
        .we_in(we_b),
        .addr_in(addr_q),
        .w_mask_in(16'hffff),
        .wd_in(data_q ^ 16'h1111)
    );

    fakeram45_256x16 u_mem2 (
        .clk(clk),
        .rd_out(rd2),
        .ce_in(ce2_b),
        .we_in(we_b),
        .addr_in(addr_q),
        .w_mask_in(16'hffff),
        .wd_in(data_q ^ 16'h2222)
    );

    fakeram45_256x16 u_mem3 (
        .clk(clk),
        .rd_out(rd3),
        .ce_in(ce3_b),
        .we_in(we_b),
        .addr_in(addr_q),
        .w_mask_in(16'hffff),
        .wd_in(data_q ^ 16'h3333)
    );

    assign gpio_out = rd0 ^ rd1 ^ rd2 ^ rd3;
endmodule
