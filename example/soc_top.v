// soc_top.v
module soc_top #(
    parameter ADDR_WIDTH = 8,
    parameter DATA_WIDTH = 32
)(
    input  wire                     clk,
    input  wire                     rst_n,
    output wire [DATA_WIDTH-1:0]    gpio_out
);

    // Wires between CPU and SRAM
    wire                     mem_en;
    wire                     mem_we;
    wire [ADDR_WIDTH-1:0]    mem_addr;
    wire [DATA_WIDTH-1:0]    mem_wdata;
    wire [DATA_WIDTH-1:0]    mem_rdata;

    // Instantiate CPU
    simple_cpu #(
        .ADDR_WIDTH(ADDR_WIDTH),
        .DATA_WIDTH(DATA_WIDTH)
    ) u_cpu (
        .clk       (clk),
        .rst_n     (rst_n),
        .mem_en    (mem_en),
        .mem_we    (mem_we),
        .mem_addr  (mem_addr),
        .mem_wdata (mem_wdata),
        .mem_rdata (mem_rdata),
        .gpio_out  (gpio_out)
    );

    // Instantiate SRAM
    simple_sram #(
        .ADDR_WIDTH(ADDR_WIDTH),
        .DATA_WIDTH(DATA_WIDTH)
    ) u_sram (
        .clk   (clk),
        .en    (mem_en),
        .we    (mem_we),
        .addr  (mem_addr),
        .wdata (mem_wdata),
        .rdata (mem_rdata)
    );

endmodule
