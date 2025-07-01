from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from fastmcp import FastMCP
import json
from ..mcp_instance import mcp  # Import the shared mcp instance

class ResourceInput(BaseModel):
    """Input schema for DB2 resources."""
    resource_type: str = Field(..., description="Type of resource to retrieve")
    filters: Optional[Dict[str, Any]] = Field(default={}, description="Filters to apply")

class ResourceResult(BaseModel):
    """Result schema for resources."""
    content: str = Field(..., description="Resource content")
    metadata: Dict[str, Any] = Field(default={}, description="Resource metadata")
    mime_type: str = Field(default="application/json", description="MIME type of the content")

@mcp.resource(name="db2_connection_guide", uri="db2://connection-guide")
def db2_connection_guide() -> ResourceResult:
    """Provide DB2 connection configuration guide."""
    guide = {
        "title": "DB2 Connection Configuration Guide",
        "description": "Step-by-step guide for configuring DB2 connections",
        "sections": [
            {
                "title": "Environment Variables",
                "content": [
                    "DB2_HOST: Database server hostname",
                    "DB2_PORT: Database port (default: 50000)",
                    "DB2_DATABASE: Database name",
                    "DB2_USERNAME: Read-only username",
                    "DB2_PASSWORD: User password"
                ]
            },
            {
                "title": "Connection String Format",
                "content": "DATABASE=dbname;HOSTNAME=host;PORT=port;PROTOCOL=TCPIP;UID=user;PWD=password;"
            },
            {
                "title": "Security Best Practices",
                "content": [
                    "Use read-only database users",
                    "Store credentials in environment variables",
                    "Enable SSL/TLS connections",
                    "Implement connection pooling"
                ]
            }
        ]
    }
    
    return ResourceResult(
        content=json.dumps(guide, indent=2),
        metadata={"type": "configuration_guide", "version": "1.0"},
        mime_type="application/json"
    )

@mcp.resource(name="db2_query_templates", uri="db2://query-templates")
def db2_query_templates() -> ResourceResult:
    """Provide common DB2 query templates."""
    templates = {
        "basic_select": "SELECT column1, column2 FROM schema.table_name WHERE condition LIMIT 100;",
        "table_info": "SELECT * FROM SYSCAT.TABLES WHERE TABSCHEMA = 'schema_name';",
        "column_info": "SELECT * FROM SYSCAT.COLUMNS WHERE TABNAME = 'table_name';",
        "index_info": "SELECT * FROM SYSCAT.INDEXES WHERE TABNAME = 'table_name';",
        "table_size": "SELECT TABSCHEMA, TABNAME, CARD FROM SYSCAT.TABLES WHERE TABSCHEMA = 'schema_name';",
        "foreign_keys": "SELECT * FROM SYSCAT.REFERENCES WHERE TABNAME = 'table_name';"
    }
    
    return ResourceResult(
        content=json.dumps(templates, indent=2),
        metadata={"type": "query_templates", "count": len(templates)},
        mime_type="application/json"
    )