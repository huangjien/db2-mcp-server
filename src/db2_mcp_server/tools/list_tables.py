"""MCP Tool to list tables in a DB2 database."""

from pydantic import BaseModel, Field
from typing import List, Optional
import ibm_db
import logging
from db2_mcp_server.cache import CacheManager
from db2_mcp_server.logger import logger
from fastmcp import FastMCP
from ..mcp_instance import mcp  # Import the shared mcp instance

# Placeholder for DB connection details - should be configured securely
# Example: Read from environment variables or a config file
DB_CONNECTION_STRING = "DATABASE=your_db;HOSTNAME=your_host;PORT=your_port;PROTOCOL=TCPIP;UID=readonly_user;PWD=your_password;" # pragma: allowlist secret

class ListTablesInput(BaseModel):
    """Input for listing tables in a DB2 database."""
    schema: Optional[str] = Field(None, description="Schema name to filter tables (optional)")
    table_type: Optional[str] = Field(None, description="Table type to filter (e.g., 'T' for tables, 'V' for views)")
    limit: Optional[int] = Field(100, description="Maximum number of tables to return")

class ListTablesResult(BaseModel):
    """Result of listing tables."""
    tables: List[str] = Field(description="List of table names")
    count: int = Field(description="Number of tables returned")
    schema_filter: Optional[str] = Field(None, description="Schema filter applied")
    table_type_filter: Optional[str] = Field(None, description="Table type filter applied")

def _list_tables_impl(ctx, args: ListTablesInput) -> ListTablesResult:
    """Internal implementation of list_tables for testing."""
    return list_tables_logic(args)

def list_tables_logic(args: ListTablesInput) -> ListTablesResult:
    """Lists tables in the configured DB2 database, optionally filtering by schema.

    Connects to the DB2 database using read-only credentials and queries
    SYSCAT.TABLES to retrieve a list of tables.
    """
    tables = []
    conn = None
    stmt = None

    try:
        # Establish read-only connection (ensure user has only SELECT)
        conn = ibm_db.connect(DB_CONNECTION_STRING, "", "") # TODO: Secure credential handling
        if not conn:
            # TODO: Improve error logging (structured)
            raise ConnectionError("Failed to connect to the DB2 database.")

        # Base query for tables (Type 'T' for Table)
        sql = "SELECT TABNAME FROM SYSCAT.TABLES WHERE TYPE = 'T'"
        params = []

        # Add schema filter if provided
        if args.schema:
            sql += " AND TABSCHEMA = ?"
            params.append(args.schema.upper()) # DB2 schema names often uppercase

        sql += " ORDER BY TABNAME"

        # Prepare and execute the statement safely
        stmt = ibm_db.prepare(conn, sql)
        if not stmt:
            # TODO: Improve error logging
            raise RuntimeError(f"Failed to prepare SQL statement: {ibm_db.stmt_errormsg()}")

        if params:
            if not ibm_db.execute(stmt, tuple(params)):
                # TODO: Improve error logging
                raise RuntimeError(f"Failed to execute SQL statement: {ibm_db.stmt_errormsg()}")
        else:
            if not ibm_db.execute(stmt):
                # TODO: Improve error logging
                raise RuntimeError(f"Failed to execute SQL statement: {ibm_db.stmt_errormsg()}")

        # Fetch results
        result = ibm_db.fetch_tuple(stmt)
        while result:
            tables.append(result[0].strip()) # Get table name
            result = ibm_db.fetch_tuple(stmt)

        return ListTablesResult(
            tables=tables,
            count=len(tables),
            schema_filter=args.schema,
            table_type_filter=args.table_type
        )

    except Exception as e:
        # TODO: Log error with context (structured logging)
        # Re-raise or return a specific error result
        # Avoid exposing raw DB errors directly if possible
        # For now, re-raise to indicate failure
        print(f"Error listing tables: {e}") # Replace with proper logging
        raise # Or return an error ToolResult

    finally:
        # Ensure resources are closed
        if stmt:
            ibm_db.free_stmt(stmt)
        if conn:
            ibm_db.close(conn)

@mcp.tool(name="list_tables")
def list_tables(ctx, args: ListTablesInput) -> ListTablesResult:
    """Lists tables in the configured DB2 database, optionally filtering by schema.

    Connects to the DB2 database using read-only credentials and queries
    SYSCAT.TABLES to retrieve a list of tables.
    """
    return list_tables_logic(args)