"""Shared MCP instance to avoid circular imports."""

import os
from mcp.server.fastmcp import FastMCP
from importlib.metadata import version, PackageNotFoundError
import logging

logger = logging.getLogger(__name__)

# --- Get Package Version ---
try:
    package_version = version("db2-mcp-server")
except PackageNotFoundError:
    logger.warning(
        "Could not determine package version using importlib.metadata. "
        "Is the package installed correctly? Falling back to 'unknown'."
    )
    package_version = "?.?.?"

# --- MCP Server Setup ---
mcp = FastMCP(
    f"DB2 MCP Server v{package_version} (DB2)",
    host="0.0.0.0",
    port=8000,
    settings={"initialization_timeout": 10, "request_timeout": 300},
)