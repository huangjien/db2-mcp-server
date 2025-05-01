from mcp.server.lowlevel.server import Server as MCPServer
from db2_mcp_server.tools.list_tables import list_tables
from db2_mcp_server.tools.get_table_metadata import get_table_metadata

# Initialize MCP Server
server = MCPServer()

# Register tools
server.register_tool(list_tables)
server.register_tool(get_table_metadata)

# Start the server
if __name__ == "__main__":
    server.start()