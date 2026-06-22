// simple_sram.v
module simple_sram #(
    parameter ADDR_WIDTH = 8,   // 2^8 = 256 word
    parameter DATA_WIDTH = 32
)(
    input  wire                     clk,
    input  wire                     en,      // chip enable
    input  wire                     we,      // write enable
    input  wire [ADDR_WIDTH-1:0]    addr,
    input  wire [DATA_WIDTH-1:0]    wdata,
    output reg  [DATA_WIDTH-1:0]    rdata
);

    // Memory array
    reg [DATA_WIDTH-1:0] mem [0:(1<<ADDR_WIDTH)-1];

    always @(posedge clk) begin
        if (en) begin
            if (we) begin
                mem[addr] <= wdata;
            end
            // synchronous read
            rdata <= mem[addr];
        end
    end

endmodule
