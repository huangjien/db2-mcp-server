import logging
import os
import sys
import argparse
import logging

# Third-party imports
from dotenv import load_dotenv
from importlib.metadata import version, PackageNotFoundError

# Local imports
from .logger import setup_logging
from .mcp_instance import mcp

# Setup logging before importing modules
setup_logging()
logger = logging.getLogger(__name__)

# --- Environment Setup ---
load_dotenv()  # Load .env file

# Import modules after mcp instance is created to avoid circular imports
from .tools import list_tables  # Import existing tools
from .prompts import db2_prompts  # Import prompts
from .resources import db2_resources  # Import resources

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
