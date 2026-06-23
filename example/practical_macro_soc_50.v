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

module practical_macro_soc_50 (
    input wire clk,
    input wire rst_n,
    input wire start,
    input wire irq_i,
    output wire [31:0] status_o
);
    localparam integer NUM_MEM = 50;

    reg [7:0] addr_base_q;
    reg [15:0] seed_q;
    reg [5:0] phase_q;

    wire active = start | irq_i;
    wire we_b = 1'b1;

    wire [NUM_MEM*16-1:0] rd_bus;
    wire [NUM_MEM*16-1:0] wd_bus;

    integer k;
    reg [31:0] status_accum_r;
    always @(*) begin
        status_accum_r = 32'h1357_2468;
        for (k = 0; k < NUM_MEM; k = k + 1) begin
            status_accum_r = status_accum_r
                           ^ {16'h0, rd_bus[(k*16) +: 16]}
                           ^ ({24'h0, k[7:0]} << (k % 5));
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            addr_base_q <= 8'h10;
            seed_q <= 16'h1a2b;
            phase_q <= 6'd0;
        end else if (active) begin
            addr_base_q <= addr_base_q + 8'h03;
            seed_q <= seed_q ^ rd_bus[15:0] ^ rd_bus[31:16] ^ {10'h0, phase_q};
            phase_q <= phase_q + 6'd1;
        end
    end

    genvar i;
    generate
        for (i = 0; i < NUM_MEM; i = i + 1) begin : gen_mem
            wire ce_in_b;
            wire [7:0] addr_in_w;
            wire [15:0] wd_in_w;

            assign ce_in_b = ~(active & (phase_q[i % 6] ^ i[0]));
            assign addr_in_w = addr_base_q + i[7:0];
            assign wd_in_w = seed_q ^ (16'h0101 * i[15:0]) ^ rd_bus[(((i + NUM_MEM - 1) % NUM_MEM) * 16) +: 16];
            assign wd_bus[(i * 16) +: 16] = wd_in_w;

            fakeram45_256x16 u_mem (
                .clk(clk),
                .rd_out(rd_bus[(i * 16) +: 16]),
                .ce_in(ce_in_b),
                .we_in(we_b),
                .addr_in(addr_in_w),
                .w_mask_in(16'hffff),
                .wd_in(wd_in_w)
            );
        end
    endgenerate

    assign status_o = status_accum_r ^ {16'h0, seed_q};
endmodule
