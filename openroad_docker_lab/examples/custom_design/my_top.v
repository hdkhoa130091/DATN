module my_top (
    input  wire       clk,
    input  wire [7:0] a,
    input  wire [7:0] b,
    output reg  [7:0] sum
);
  always @(posedge clk) begin
    sum <= a + b;
  end
endmodule
