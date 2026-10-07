from mcp.server.fastmcp import FastMCP




# Create MCP server
mcp = FastMCP("My First MCP Server")




# --------------------------------------------------
# TOOL 1: Addition
# --------------------------------------------------


@mcp.tool()
def add_numbers(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b




# --------------------------------------------------
# TOOL 2: Multiplication
# --------------------------------------------------


@mcp.tool()
def multiply_numbers(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b




# --------------------------------------------------
# Start MCP server
# --------------------------------------------------


if __name__ == "__main__":
    mcp.run()
