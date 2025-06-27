import logging
import os
import sys
import argparse
import logging

# Third-party imports
from dotenv import load_dotenv
from importlib.metadata import version, PackageNotFoundError

# MCP imports
from mcp.server.fastmcp import FastMCP
# Local imports
from .logger import setup_logging

# Setup logging before importing github/jenkins
setup_logging()
logger = logging.getLogger(__name__)

# --- Environment Setup ---
load_dotenv()  # Load .env file

# --- Get Package Version ---
try:
  # Replace 'db2-mcp-server' if your actual distributable package name is different
  # This name usually comes from your pyproject.toml `[project] name`
  # or setup.py `name=` argument.
  package_version = version("db2-mcp-server")
except PackageNotFoundError:
  logger.warning(
    "Could not determine package version using importlib.metadata. "
    "Is the package installed correctly? Falling back to 'unknown'."
  )
  package_version = "?.?.?"  # Provide a fallback

# --- MCP Server Setup ---

mcp = FastMCP(
  f"DB2 MCP Server v{package_version} (DB2)",
  host="0.0.0.0",
  port=8000,
  settings={"initialization_timeout": 10, "request_timeout": 300},
)

def main():
  """Entry point for the CLI."""
  parser = argparse.ArgumentParser(
    description="DevOps MCP Server (PyGithub - Raw Output)"
  )
  parser.add_argument(
    "--transport",
    choices=["stdio", "stream_http"],
    default="stdio",
    help="Transport type (stdio or stream_http)",
  )

  args = parser.parse_args()
  if args.transport == "stream_http":
    port = int(os.getenv("MCP_PORT", "3721"))
    mcp.run(transport="http", host="127.0.0.1", port=port, path="/mcp")
  else:
    mcp.run(transport=args.transport)


def main_stream_http():
  """Run the MCP server with stream_http transport."""
  if "--transport" not in sys.argv:
    sys.argv.extend(["--transport", "stream_http"])
  elif "stream_http" not in sys.argv:
    try:
      idx = sys.argv.index("--transport")
      if idx + 1 < len(sys.argv):
        sys.argv[idx + 1] = "stream_http"
      else:
        sys.argv.append("stream_http")
    except ValueError:
      sys.argv.extend(["--transport", "stream_http"])

  main()


if __name__ == "__main__":
  main()
