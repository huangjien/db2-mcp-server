import pytest
from unittest.mock import MagicMock, patch
from db2_mcp_server.core import server
from db2_mcp_server.tools.list_tables import list_tables
from db2_mcp_server.tools.get_table_metadata import get_table_metadata

@pytest.fixture
def mock_server():
    """Provides a mock MCPServer."""
    return MagicMock(spec=server)

@patch('db2_mcp_server.core.server')
def test_server_initialization(mock_server):
    """Test server initialization and tool registration."""
    # Arrange
    mock_server.register_tool = MagicMock()

    # Act
    server.register_tool(list_tables)
    server.register_tool(get_table_metadata)

    # Assert
    mock_server.register_tool.assert_any_call(list_tables)
    mock_server.register_tool.assert_any_call(get_table_metadata)

@patch('db2_mcp_server.core.server')
def test_server_start(mock_server):
    """Test server start without errors."""
    # Arrange
    mock_server.start = MagicMock()

    # Act
    server.start()

    # Assert
    mock_server.start.assert_called_once()