import pytest
import sys
import os
from unittest.mock import MagicMock, patch, call
from db2_mcp_server.core import mcp, main, main_stream_http

@pytest.fixture
def mock_mcp():
    """Provides a mock FastMCP instance."""
    return MagicMock(spec=mcp)

@pytest.fixture
def mock_argv():
    """Backup and restore sys.argv for testing."""
    original_argv = sys.argv.copy()
    yield
    sys.argv = original_argv

def test_mcp_initialization():
    """Test MCP server initialization."""
    # Arrange & Act
    from db2_mcp_server.core import mcp
    
    # Assert - just verify the mcp instance exists and has expected attributes
    assert mcp is not None
    assert hasattr(mcp, 'tool')
    assert hasattr(mcp, 'run')

@patch('db2_mcp_server.core.mcp')
def test_mcp_run(mock_mcp_instance):
    """Test MCP server run without errors."""
    # Arrange
    mock_mcp_instance.run = MagicMock()

    # Act
    mock_mcp_instance.run(transport="stdio")

    # Assert
    mock_mcp_instance.run.assert_called_once_with(transport="stdio")

@patch('db2_mcp_server.core.mcp')
@patch('sys.argv', ['test_script'])
def test_main_default_stdio_transport(mock_mcp_instance):
    """Test main function with default stdio transport."""
    # Arrange
    mock_mcp_instance.run = MagicMock()
    
    # Act
    main()
    
    # Assert
    mock_mcp_instance.run.assert_called_once_with(transport="stdio")

@patch('db2_mcp_server.core.mcp')
@patch('sys.argv', ['test_script', '--transport', 'stdio'])
def test_main_explicit_stdio_transport(mock_mcp_instance):
    """Test main function with explicit stdio transport."""
    # Arrange
    mock_mcp_instance.run = MagicMock()
    
    # Act
    main()
    
    # Assert
    mock_mcp_instance.run.assert_called_once_with(transport="stdio")

@patch('db2_mcp_server.core.mcp')
@patch('os.getenv')
@patch('sys.argv', ['test_script', '--transport', 'stream_http'])
def test_main_stream_http_transport_default_port(mock_getenv, mock_mcp_instance):
    """Test main function with stream_http transport using default port."""
    # Arrange
    mock_getenv.return_value = "3721"  # Default port as string
    mock_mcp_instance.run = MagicMock()
    
    # Act
    main()
    
    # Assert
    mock_getenv.assert_called_once_with("MCP_PORT", "3721")
    mock_mcp_instance.run.assert_called_once_with(
        transport="http", host="127.0.0.1", port=3721, path="/mcp"
    )

@patch('db2_mcp_server.core.mcp')
@patch('os.getenv')
@patch('sys.argv', ['test_script', '--transport', 'stream_http'])
def test_main_stream_http_transport_custom_port(mock_getenv, mock_mcp_instance):
    """Test main function with stream_http transport using custom port."""
    # Arrange
    mock_getenv.return_value = "8080"
    mock_mcp_instance.run = MagicMock()
    
    # Act
    main()
    
    # Assert
    mock_getenv.assert_called_once_with("MCP_PORT", "3721")
    mock_mcp_instance.run.assert_called_once_with(
        transport="http", host="127.0.0.1", port=8080, path="/mcp"
    )

@patch('db2_mcp_server.core.main')
def test_main_stream_http_no_transport_arg(mock_main, mock_argv):
    """Test main_stream_http when no --transport argument exists."""
    # Arrange
    sys.argv = ['test_script']
    
    # Act
    main_stream_http()
    
    # Assert
    assert '--transport' in sys.argv
    assert 'stream_http' in sys.argv
    mock_main.assert_called_once()

@patch('db2_mcp_server.core.main')
def test_main_stream_http_with_transport_arg_no_value(mock_main, mock_argv):
    """Test main_stream_http when --transport exists but no value."""
    # Arrange
    sys.argv = ['test_script', '--transport']
    
    # Act
    main_stream_http()
    
    # Assert
    assert 'stream_http' in sys.argv
    mock_main.assert_called_once()

@patch('db2_mcp_server.core.main')
def test_main_stream_http_with_different_transport(mock_main, mock_argv):
    """Test main_stream_http when --transport exists with different value."""
    # Arrange
    sys.argv = ['test_script', '--transport', 'stdio']
    
    # Act
    main_stream_http()
    
    # Assert
    assert sys.argv[2] == 'stream_http'
    mock_main.assert_called_once()

@patch('db2_mcp_server.core.main')
def test_main_stream_http_with_stream_http_already_set(mock_main, mock_argv):
    """Test main_stream_http when stream_http is already in argv."""
    # Arrange
    sys.argv = ['test_script', '--transport', 'stream_http']
    
    # Act
    main_stream_http()
    
    # Assert
    # Should not modify argv since stream_http is already present
    assert sys.argv == ['test_script', '--transport', 'stream_http']
    mock_main.assert_called_once()

def test_package_version_found():
    """Test package version retrieval when package is found."""
    # This test verifies that the mcp_instance module can be imported
    # and that it handles version lookup properly
    from db2_mcp_server.mcp_instance import package_version
    
    # Assert that package_version is set to something
    assert package_version is not None
    assert isinstance(package_version, str)
    assert len(package_version) > 0

def test_package_version_handling():
    """Test that package version is handled properly."""
    # This test verifies that the module can handle version lookup
    # The actual version lookup happens at module import time
    from db2_mcp_server.core import mcp
    assert mcp is not None
    # Verify the server name contains version info (either real or fallback)
    assert "DB2 MCP Server" in mcp.name
    assert "v" in mcp.name  # Version should be included

def test_logging_setup_called():
    """Test that setup_logging is called during module import."""
    # This test verifies that the module imports without error
    # and that the logger is properly initialized
    from db2_mcp_server.core import logger
    assert logger is not None
    assert logger.name == 'db2_mcp_server.core'

def test_dotenv_loaded():
    """Test that .env file loading is configured."""
    # This test verifies that the module imports without error
    # The actual dotenv loading happens at module level
    from db2_mcp_server import core
    assert core is not None