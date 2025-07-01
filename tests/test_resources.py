import pytest
import json
from src.db2_mcp_server.resources.db2_resources import db2_connection_guide, ResourceInput

def test_db2_connection_guide():
    result = db2_connection_guide()
    content = json.loads(result.content)
    assert "title" in content
    assert result.mime_type == "application/json"