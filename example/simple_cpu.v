// simple_cpu.v
module simple_cpu #(
    parameter ADDR_WIDTH = 8,
    parameter DATA_WIDTH = 32
)(
    input  wire                     clk,
    input  wire                     rst_n,

    // Interface to SRAM
    output reg                      mem_en,
    output reg                      mem_we,
    output reg  [ADDR_WIDTH-1:0]    mem_addr,
    output reg  [DATA_WIDTH-1:0]    mem_wdata,
    input  wire [DATA_WIDTH-1:0]    mem_rdata,

    // Simple output to observe result
    output reg  [DATA_WIDTH-1:0]    gpio_out
);

    // Simple state machine
    localparam ST_IDLE     = 3'd0;
    localparam ST_WRITE0   = 3'd1;
    localparam ST_WRITE1   = 3'd2;
    localparam ST_READ0    = 3'd3;
    localparam ST_READ1    = 3'd4;
    localparam ST_DONE     = 3'd5;

    reg [2:0]  state, next_state;

    // registers to hold read data
    reg [DATA_WIDTH-1:0] r0;
    reg [DATA_WIDTH-1:0] r1;

    // Sequential part
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state    <= ST_IDLE;
            r0       <= {DATA_WIDTH{1'b0}};
            r1       <= {DATA_WIDTH{1'b0}};
            gpio_out <= {DATA_WIDTH{1'b0}};
        end else begin
            state <= next_state;

            // capture read data
            case (state)
                ST_READ0: r0 <= mem_rdata;
                ST_READ1: r1 <= mem_rdata;
                ST_DONE:  gpio_out <= r0 + r1;
                default:  ;
            endcase
        end
    end

    // Combinational part
    always @* begin
        // default
        mem_en   = 1'b0;
        mem_we   = 1'b0;
        mem_addr = {ADDR_WIDTH{1'b0}};
        mem_wdata = {DATA_WIDTH{1'b0}};
        next_state = state;

        case (state)
            ST_IDLE: begin
                // start sequence
                mem_en = 1'b0;
                next_state = ST_WRITE0;
            end

            ST_WRITE0: begin
                mem_en   = 1'b1;
                mem_we   = 1'b1;
                mem_addr = {ADDR_WIDTH{1'b0}}; // address 0
                mem_wdata = 32'd10;            // write 10
                next_state = ST_WRITE1;
            end

            ST_WRITE1: begin
                mem_en   = 1'b1;
                mem_we   = 1'b1;
                mem_addr = {{(ADDR_WIDTH-1){1'b0}}, 1'b1}; // address 1
                mem_wdata = 32'd20;           // write 20
                next_state = ST_READ0;
            end

            ST_READ0: begin
                mem_en   = 1'b1;
                mem_we   = 1'b0;
                mem_addr = {ADDR_WIDTH{1'b0}}; // read addr 0
                next_state = ST_READ1;
            end

            ST_READ1: begin
                mem_en   = 1'b1;
                mem_we   = 1'b0;
                mem_addr = {{(ADDR_WIDTH-1){1'b0}}, 1'b1}; // read addr 1
                next_state = ST_DONE;
            end

            ST_DONE: begin
                mem_en = 1'b0;
                mem_we = 1'b0;
                next_state = ST_DONE; // stay here
            end

            default: begin
                next_state = ST_IDLE;
            end
        endcase
    end

endmodule
