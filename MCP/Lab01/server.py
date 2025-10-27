#!/usr/bin/env python3
import logging
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# === 1) Logging ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("MultiplyFastMCPServer")

# === 2) Env (optional) ===
load_dotenv()

# === 3) MCP Server ===
mcp = FastMCP("Math Tools MCP")

# === 4) Tool ===
@mcp.tool(
    name="multiply",
    description="Multiply two numbers and return the product."
)
async def multiply(a: float, b: float) -> dict:
    """
    Args:
        a: First number
        b: Second number
    Returns:
        { "a": a, "b": b, "product": a*b }
    """
    logger.info("🚀 multiply called with a=%s, b=%s", a, b)
    product = a * b
    return {
        "a": a,
        "b": b,
        "product": product,
        "summary": f"{a} × {b} = {product}"
    }

# === 5) Entrypoint ===
if __name__ == "__main__":
    logger.info("Starting Math Tools MCP (stdio)")
    mcp.run(transport="stdio")
