"""Tests for the list_tables MCP tool."""

import pytest
from unittest.mock import MagicMock, patch

# Assuming the tool file is correctly placed for import
# Adjust the import path based on your project structure and how you run pytest
from db2_mcp_server.tools.list_tables import (
    ListTablesInput,
    ListTablesResult,
    DB_CONNECTION_STRING, # Import for patching
    list_tables_logic,
)
# --- Test Cases ---

@patch('db2_mcp_server.tools.list_tables.ibm_db')
def test_list_tables_success_no_filter(mock_ibm_db):
    """Test successful listing of tables without a schema filter."""
    # Arrange Mocks
    mock_conn = MagicMock()
    mock_stmt = MagicMock()
    mock_ibm_db.connect.return_value = mock_conn
    mock_ibm_db.prepare.return_value = mock_stmt
    mock_ibm_db.execute.return_value = True
    # Simulate fetching two tables
    mock_ibm_db.fetch_tuple.side_effect = [('TABLE1 ',), ('TABLE2 ',), None]

    args = ListTablesInput(schema=None)

    # Act
    result = list_tables_logic(args)

    # Assert
    assert isinstance(result, ListTablesResult)
    assert result.tables == ["TABLE1", "TABLE2"]
    assert result.count == 2
    assert result.schema_filter is None
    assert result.table_type_filter is None
    mock_ibm_db.connect.assert_called_once_with(DB_CONNECTION_STRING, "", "")
    mock_ibm_db.prepare.assert_called_once_with(mock_conn, "SELECT TABNAME FROM SYSCAT.TABLES WHERE TYPE = 'T' ORDER BY TABNAME")
    mock_ibm_db.execute.assert_called_once_with(mock_stmt)
    mock_ibm_db.close.assert_called_once_with(mock_conn)
    mock_ibm_db.free_stmt.assert_called_once_with(mock_stmt)

@patch('db2_mcp_server.tools.list_tables.ibm_db')
def test_list_tables_success_with_filter(mock_ibm_db):
    """Test successful listing of tables with a schema filter."""
    # Arrange Mocks
    mock_conn = MagicMock()
    mock_stmt = MagicMock()
    mock_ibm_db.connect.return_value = mock_conn
    mock_ibm_db.prepare.return_value = mock_stmt
    mock_ibm_db.execute.return_value = True
    mock_ibm_db.fetch_tuple.side_effect = [('TABLE_A',), None]

    schema = "MYSCHEMA"
    args = ListTablesInput(schema=schema)

    # Act
    result = list_tables_logic(args)

    # Assert
    assert isinstance(result, ListTablesResult)
    assert result.tables == ["TABLE_A"]
    assert result.count == 1
    assert result.schema_filter == "MYSCHEMA"
    assert result.table_type_filter is None
    mock_ibm_db.connect.assert_called_once_with(DB_CONNECTION_STRING, "", "")
    expected_sql = "SELECT TABNAME FROM SYSCAT.TABLES WHERE TYPE = 'T' AND TABSCHEMA = ? ORDER BY TABNAME"
    mock_ibm_db.prepare.assert_called_once_with(mock_conn, expected_sql)
    mock_ibm_db.execute.assert_called_once_with(mock_stmt, (schema.upper(),))
    mock_ibm_db.close.assert_called_once_with(mock_conn)
    mock_ibm_db.free_stmt.assert_called_once_with(mock_stmt)

@patch('db2_mcp_server.tools.list_tables.ibm_db')
def test_list_tables_connection_error(mock_ibm_db):
    """Test handling of a database connection error."""
    # Arrange Mocks
    mock_ibm_db.connect.return_value = None # Simulate connection failure

    args = ListTablesInput(schema=None)

    # Act & Assert
    with pytest.raises(ConnectionError, match="Failed to connect to the DB2 database."):
        list_tables_logic(args)

    mock_ibm_db.connect.assert_called_once_with(DB_CONNECTION_STRING, "", "")
    mock_ibm_db.prepare.assert_not_called()
    mock_ibm_db.execute.assert_not_called()
    mock_ibm_db.close.assert_not_called() # Connection wasn't established
    mock_ibm_db.free_stmt.assert_not_called()

@patch('db2_mcp_server.tools.list_tables.ibm_db')
def test_list_tables_prepare_error(mock_ibm_db):
    """Test handling of a statement preparation error."""
    # Arrange Mocks
    mock_conn = MagicMock()
    mock_ibm_db.connect.return_value = mock_conn
    mock_ibm_db.prepare.return_value = None # Simulate prepare failure
    mock_ibm_db.stmt_errormsg.return_value = "Syntax error"

    args = ListTablesInput(schema=None)

    # Act & Assert
    with pytest.raises(RuntimeError, match="Failed to prepare SQL statement: Syntax error"):
        list_tables_logic(args)

    mock_ibm_db.connect.assert_called_once_with(DB_CONNECTION_STRING, "", "")
    mock_ibm_db.prepare.assert_called_once()
    mock_ibm_db.execute.assert_not_called()
    mock_ibm_db.close.assert_called_once_with(mock_conn)
    mock_ibm_db.free_stmt.assert_not_called() # Stmt wasn't created

@patch('db2_mcp_server.tools.list_tables.ibm_db')
def test_list_tables_execute_error(mock_ibm_db):
    """Test handling of a statement execution error."""
    # Arrange Mocks
    mock_conn = MagicMock()
    mock_stmt = MagicMock()
    mock_ibm_db.connect.return_value = mock_conn
    mock_ibm_db.prepare.return_value = mock_stmt
    mock_ibm_db.execute.return_value = False # Simulate execute failure
    mock_ibm_db.stmt_errormsg.return_value = "Table not found"

    args = ListTablesInput(schema=None)

    # Act & Assert
    with pytest.raises(RuntimeError, match="Failed to execute SQL statement: Table not found"):
        list_tables_logic(args)

    mock_ibm_db.connect.assert_called_once_with(DB_CONNECTION_STRING, "", "")
    mock_ibm_db.prepare.assert_called_once()
    mock_ibm_db.execute.assert_called_once()
    mock_ibm_db.close.assert_called_once_with(mock_conn)
    mock_ibm_db.free_stmt.assert_called_once_with(mock_stmt)

@patch('db2_mcp_server.tools.list_tables.ibm_db')
def test_list_tables_no_tables_found(mock_ibm_db):
    """Test the scenario where no tables are found."""
    # Arrange Mocks
    mock_conn = MagicMock()
    mock_stmt = MagicMock()
    mock_ibm_db.connect.return_value = mock_conn
    mock_ibm_db.prepare.return_value = mock_stmt
    mock_ibm_db.execute.return_value = True
    mock_ibm_db.fetch_tuple.return_value = None # No results

    args = ListTablesInput(schema=None)

    # Act
    result = list_tables_logic(args)

    # Assert
    assert isinstance(result, ListTablesResult)
    assert result.tables == []
    assert result.count == 0
    assert result.schema_filter is None
    assert result.table_type_filter is None
    mock_ibm_db.connect.assert_called_once_with(DB_CONNECTION_STRING, "", "")
    mock_ibm_db.prepare.assert_called_once()
    mock_ibm_db.execute.assert_called_once()
    mock_ibm_db.close.assert_called_once_with(mock_conn)
    mock_ibm_db.free_stmt.assert_called_once_with(mock_stmt)

@patch('db2_mcp_server.tools.list_tables.ibm_db')
def test_list_tables_empty_schema(mock_ibm_db):
    """Test listing tables with an empty schema filter."""
    # Arrange Mocks
    mock_conn = MagicMock()
    mock_stmt = MagicMock()
    mock_ibm_db.connect.return_value = mock_conn
    mock_ibm_db.prepare.return_value = mock_stmt
    mock_ibm_db.execute.return_value = True
    mock_ibm_db.fetch_tuple.side_effect = [('TABLE1',), ('TABLE2',), None]

    args = ListTablesInput(schema="")

    # Act
    result = list_tables_logic(args)

    # Assert
    assert isinstance(result, ListTablesResult)
    assert result.tables == ["TABLE1", "TABLE2"]
    assert result.count == 2
    assert result.schema_filter == ""
    assert result.table_type_filter is None
    mock_ibm_db.connect.assert_called_once_with(DB_CONNECTION_STRING, "", "")
    mock_ibm_db.prepare.assert_called_once_with(mock_conn, "SELECT TABNAME FROM SYSCAT.TABLES WHERE TYPE = 'T' ORDER BY TABNAME")
    mock_ibm_db.execute.assert_called_once_with(mock_stmt)
    mock_ibm_db.close.assert_called_once_with(mock_conn)
    mock_ibm_db.free_stmt.assert_called_once_with(mock_stmt)

@patch('db2_mcp_server.tools.list_tables.ibm_db')
def test_list_tables_null_schema(mock_ibm_db):
    """Test listing tables with a null schema filter."""
    # Arrange Mocks
    mock_conn = MagicMock()
    mock_stmt = MagicMock()
    mock_ibm_db.connect.return_value = mock_conn
    mock_ibm_db.prepare.return_value = mock_stmt
    mock_ibm_db.execute.return_value = True
    mock_ibm_db.fetch_tuple.side_effect = [('TABLE1',), ('TABLE2',), None]

    args = ListTablesInput(schema=None)

    # Act
    result = list_tables_logic(args)

    # Assert
    assert isinstance(result, ListTablesResult)
    assert result.tables == ["TABLE1", "TABLE2"]
    mock_ibm_db.connect.assert_called_once_with(DB_CONNECTION_STRING, "", "")
    mock_ibm_db.prepare.assert_called_once_with(mock_conn, "SELECT TABNAME FROM SYSCAT.TABLES WHERE TYPE = 'T' ORDER BY TABNAME")
    mock_ibm_db.execute.assert_called_once_with(mock_stmt)
    mock_ibm_db.close.assert_called_once_with(mock_conn)
    mock_ibm_db.free_stmt.assert_called_once_with(mock_stmt)

@patch('db2_mcp_server.tools.list_tables.ibm_db')
def test_list_tables_database_error(mock_ibm_db):
    """Test handling of a database error during table listing."""
    # Arrange Mocks
    mock_conn = MagicMock()
    mock_stmt = MagicMock()
    mock_ibm_db.connect.return_value = mock_conn
    mock_ibm_db.prepare.return_value = mock_stmt
    mock_ibm_db.execute.side_effect = Exception("Database error")

    args = ListTablesInput(schema=None)

    # Act & Assert
    with pytest.raises(Exception, match="Database error"):
        list_tables_logic(args)

    mock_ibm_db.connect.assert_called_once_with(DB_CONNECTION_STRING, "", "")
    mock_ibm_db.prepare.assert_called_once()
    mock_ibm_db.execute.assert_called_once()
    mock_ibm_db.close.assert_called_once_with(mock_conn)
    mock_ibm_db.free_stmt.assert_called_once_with(mock_stmt)