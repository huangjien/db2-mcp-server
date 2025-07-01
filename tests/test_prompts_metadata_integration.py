"""Tests for table metadata integration in db2_prompts.py."""

from unittest.mock import Mock, patch

import pytest

from db2_mcp_server.prompts.db2_prompts import (
    store_table_metadata_from_context,
    get_stored_table_info,
    list_stored_tables,
    dynamic_prompt,
    PromptInput,
)
from db2_mcp_server.storage.table_metadata import FieldInfo, TableMetadata


class TestStoreTableMetadataFromContext:
    """Test store_table_metadata_from_context function."""

    @patch('db2_mcp_server.prompts.db2_prompts.get_table_metadata_storage')
    @patch('db2_mcp_server.prompts.db2_prompts.parse_field_descriptions')
    @patch('db2_mcp_server.prompts.db2_prompts.extract_table_name_from_context')
    def test_store_metadata_success(self, mock_extract_table, mock_parse_fields, mock_get_storage):
        """Test successful metadata storage from context."""
        # Setup mocks
        mock_extract_table.return_value = "users"
        mock_parse_fields.return_value = {
            "id": "Primary key",
            "name": "User name"
        }
        mock_storage = Mock()
        mock_storage.bulk_update_from_descriptions.return_value = True
        mock_get_storage.return_value = mock_storage
        
        context = "TABLE: users\nid: Primary key\nname: User name"
        
        result = store_table_metadata_from_context(context)
        
        assert result is True
        mock_extract_table.assert_called_once_with(context)
        mock_parse_fields.assert_called_once_with(context)
        mock_storage.bulk_update_from_descriptions.assert_called_once_with(
            table_name="users", field_descriptions={"id": "Primary key", "name": "User name"}
        )

    @patch('db2_mcp_server.prompts.db2_prompts.get_table_metadata_storage')
    @patch('db2_mcp_server.prompts.db2_prompts.parse_field_descriptions')
    @patch('db2_mcp_server.prompts.db2_prompts.extract_table_name_from_context')
    def test_store_metadata_no_table_name(self, mock_extract_table, mock_parse_fields, mock_get_storage):
        """Test metadata storage when no table name found."""
        mock_extract_table.return_value = None
        mock_parse_fields.return_value = {"id": "Primary key"}
        
        context = "id: Primary key"
        
        result = store_table_metadata_from_context(context)
        
        assert result is False
        mock_extract_table.assert_called_once_with(context)
        mock_parse_fields.assert_not_called()

    @patch('db2_mcp_server.prompts.db2_prompts.get_table_metadata_storage')
    @patch('db2_mcp_server.prompts.db2_prompts.parse_field_descriptions')
    @patch('db2_mcp_server.prompts.db2_prompts.extract_table_name_from_context')
    def test_store_metadata_no_fields(self, mock_extract_table, mock_parse_fields, mock_get_storage):
        """Test metadata storage when no fields found."""
        mock_extract_table.return_value = "users"
        mock_parse_fields.return_value = {}
        
        context = "TABLE: users"
        
        result = store_table_metadata_from_context(context)
        
        assert result is False
        mock_extract_table.assert_called_once_with(context)
        mock_parse_fields.assert_called_once_with(context)

    @patch('db2_mcp_server.prompts.db2_prompts.get_table_metadata_storage')
    @patch('db2_mcp_server.prompts.db2_prompts.parse_field_descriptions')
    @patch('db2_mcp_server.prompts.db2_prompts.extract_table_name_from_context')
    def test_store_metadata_storage_failure(self, mock_extract_table, mock_parse_fields, mock_get_storage):
        """Test metadata storage when storage operation fails."""
        mock_extract_table.return_value = "users"
        mock_parse_fields.return_value = {"id": "Primary key"}
        mock_storage = Mock()
        mock_storage.bulk_update_from_descriptions.return_value = False
        mock_get_storage.return_value = mock_storage
        
        context = "TABLE: users\nid: Primary key"
        
        result = store_table_metadata_from_context(context)
        
        assert result is False


class TestGetStoredTableInfo:
    """Test get_stored_table_info function."""

    @patch('db2_mcp_server.prompts.db2_prompts.get_table_metadata_storage')
    def test_get_stored_info_success(self, mock_get_storage):
        """Test successful retrieval of stored table info."""
        # Setup mock metadata
        mock_metadata = TableMetadata(
            table_name="users",
            schema_name="public",
            description="User information table",
            fields=[
                FieldInfo(name="id", description="Primary key"),
                FieldInfo(name="name", description="User name")
            ]
        )
        
        mock_storage = Mock()
        mock_storage.get_table_metadata.return_value = mock_metadata
        mock_get_storage.return_value = mock_storage
        
        result = get_stored_table_info("users")
        
        assert "TABLE: users" in result
        assert "DESCRIPTION: User information table" in result
        assert "id: Primary key" in result
        assert "name: User name" in result
        mock_storage.get_table_metadata.assert_called_once_with("users", None)

    @patch('db2_mcp_server.prompts.db2_prompts.get_table_metadata_storage')
    def test_get_stored_info_no_metadata(self, mock_get_storage):
        """Test when no metadata is stored for table."""
        mock_storage = Mock()
        mock_storage.get_table_metadata.return_value = None
        mock_get_storage.return_value = mock_storage
        
        result = get_stored_table_info("unknown_table")
        
        assert result is None
        mock_storage.get_table_metadata.assert_called_once_with("unknown_table", None)

    @patch('db2_mcp_server.prompts.db2_prompts.get_table_metadata_storage')
    def test_get_stored_info_no_business_context(self, mock_get_storage):
        """Test table info without business context."""
        mock_metadata = TableMetadata(
            table_name="simple_table",
            description=None,
            fields=[
                FieldInfo(name="id", description="Primary key")
            ]
        )
        
        mock_storage = Mock()
        mock_storage.get_table_metadata.return_value = mock_metadata
        mock_get_storage.return_value = mock_storage
        
        result = get_stored_table_info("simple_table")
        
        assert "TABLE: simple_table" in result
        assert "DESCRIPTION:" not in result  # No description provided
        assert "id: Primary key" in result


class TestListStoredTables:
    """Test list_stored_tables function."""

    @patch('db2_mcp_server.prompts.db2_prompts.get_table_metadata_storage')
    def test_list_stored_tables_success(self, mock_get_storage):
        """Test successful listing of stored tables."""
        mock_storage = Mock()
        mock_storage.list_stored_tables.return_value = ["users", "orders", "products"]
        mock_get_storage.return_value = mock_storage
        
        result = list_stored_tables()
        
        assert result == ["users", "orders", "products"]
        mock_storage.list_stored_tables.assert_called_once()

    @patch('db2_mcp_server.prompts.db2_prompts.get_table_metadata_storage')
    def test_list_stored_tables_empty(self, mock_get_storage):
        """Test listing when no tables are stored."""
        mock_storage = Mock()
        mock_storage.list_stored_tables.return_value = []
        mock_get_storage.return_value = mock_storage
        
        result = list_stored_tables()
        
        assert result == []
        mock_storage.list_stored_tables.assert_called_once()


class TestDynamicPromptIntegration:
    """Test dynamic_prompt integration with table metadata."""

    @patch('db2_mcp_server.prompts.db2_prompts.store_table_metadata_from_context')
    @patch('db2_mcp_server.prompts.db2_prompts.get_stored_table_info')
    @patch('db2_mcp_server.prompts.db2_prompts.dynamic_loader')
    def test_dynamic_prompt_data_explainer_with_context(self, mock_loader, mock_get_info, mock_store):
        """Test dynamic_prompt with data_explainer and context containing field descriptions."""
        
        # Setup mocks
        mock_loader.get_prompt.return_value = {"template": "Test template"}
        mock_loader.generate_prompt_text.return_value = "Generated prompt"
        mock_loader.get_suggestions.return_value = ["Test suggestion"]
        mock_store.return_value = True
        mock_get_info.return_value = "Stored table info"
        
        context = "TABLE: users\nid: Primary key\nname: User name"
        args = PromptInput(prompt_name="data_explainer", context=context, table_name="users")
        ctx = {}
        
        result = dynamic_prompt(ctx, args)
        
        assert result.prompt == "Generated prompt"
        assert any("field descriptions" in suggestion for suggestion in result.suggestions)
        mock_store.assert_called_once_with(context, "users")

    @patch('db2_mcp_server.prompts.db2_prompts.store_table_metadata_from_context')
    @patch('db2_mcp_server.prompts.db2_prompts.get_stored_table_info')
    @patch('db2_mcp_server.prompts.db2_prompts.dynamic_loader')
    def test_dynamic_prompt_data_explainer_no_stored_metadata(self, mock_loader, mock_get_info, mock_store):
        """Test dynamic_prompt with data_explainer when no stored metadata exists."""
        
        # Setup mocks
        mock_loader.get_prompt.return_value = {"template": "Test template"}
        mock_loader.generate_prompt_text.return_value = "Generated prompt"
        mock_loader.get_suggestions.return_value = ["Test suggestion"]
        mock_store.return_value = False
        mock_get_info.return_value = None
        
        args = PromptInput(prompt_name="data_explainer", context="", table_name="unknown_table")
        ctx = {}
        
        result = dynamic_prompt(ctx, args)
        
        assert result.prompt == "Generated prompt"
        assert any("field descriptions" in suggestion for suggestion in result.suggestions)
        mock_get_info.assert_called_once_with("unknown_table")

    @patch('db2_mcp_server.prompts.db2_prompts.store_table_metadata_from_context')
    @patch('db2_mcp_server.prompts.db2_prompts.get_stored_table_info')
    @patch('db2_mcp_server.prompts.db2_prompts.dynamic_loader')
    def test_dynamic_prompt_non_data_explainer(self, mock_loader, mock_get_info, mock_store):
        """Test dynamic_prompt with non-data_explainer prompt."""
        
        # Setup mocks
        mock_loader.get_prompt.return_value = {"template": "Test template"}
        mock_loader.generate_prompt_text.return_value = "Generated prompt"
        mock_loader.get_suggestions.return_value = ["Test suggestion"]
        
        args = PromptInput(prompt_name="other_prompt", context="Some context")
        ctx = {}
        
        result = dynamic_prompt(ctx, args)
        
        assert result.prompt == "Generated prompt"
        mock_store.assert_not_called()
        mock_get_info.assert_not_called()

    @patch('db2_mcp_server.prompts.db2_prompts.store_table_metadata_from_context')
    @patch('db2_mcp_server.prompts.db2_prompts.get_stored_table_info')
    @patch('db2_mcp_server.prompts.db2_prompts.dynamic_loader')
    def test_dynamic_prompt_data_explainer_enhanced_context(self, mock_loader, mock_get_info, mock_store):
        """Test dynamic_prompt with enhanced context from stored metadata."""
        
        # Setup mocks
        mock_loader.get_prompt.return_value = {"template": "Test template"}
        mock_loader.generate_prompt_text.return_value = "Generated prompt"
        mock_loader.get_suggestions.return_value = ["Test suggestion"]
        mock_store.return_value = False
        mock_get_info.return_value = "\nStored metadata:\nid: Primary key"
        
        original_context = "Original context"
        args = PromptInput(prompt_name="data_explainer", context=original_context, table_name="users")
        ctx = {}
        
        result = dynamic_prompt(ctx, args)
        
        # Check that generate_prompt_text was called with enhanced context
        mock_loader.generate_prompt_text.assert_called_once()
        assert result.prompt == "Generated prompt"

    @patch('db2_mcp_server.prompts.db2_prompts.dynamic_loader')
    def test_dynamic_prompt_prompt_not_found(self, mock_loader):
        """Test dynamic_prompt when prompt is not found."""
        
        mock_loader.get_prompt.return_value = None
        mock_loader.list_prompts.return_value = []
        
        args = PromptInput(prompt_name="nonexistent_prompt")
        ctx = {}
        
        result = dynamic_prompt(ctx, args)
        
        assert "Dynamic prompt loading failed" in result.prompt
        assert "Check PROMPTS_FILE environment variable" in result.suggestions