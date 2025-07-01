"""Comprehensive unit tests for db2_prompts.py module.

This test file adds additional coverage for functions and edge cases
not fully covered by existing test files.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Optional

from src.db2_mcp_server.prompts.db2_prompts import (
    db2_query_helper,
    db2_schema_analyzer,
    dynamic_prompt,
    get_available_dynamic_prompts,
    reload_dynamic_prompts,
    has_dynamic_prompts,
    store_table_metadata_from_context,
    get_stored_table_info,
    list_stored_tables,
    PromptInput,
    PromptResult
)
from src.db2_mcp_server.storage.table_metadata import FieldInfo, TableMetadata


class TestPromptModels:
    """Test PromptInput and PromptResult models."""
    
    def test_prompt_input_creation(self):
        """Test PromptInput model creation with various parameters."""
        # Test with all parameters
        prompt_input = PromptInput(
            table_name="users",
            context="Test context",
            prompt_name="test_prompt"
        )
        assert prompt_input.table_name == "users"
        assert prompt_input.context == "Test context"
        assert prompt_input.prompt_name == "test_prompt"
    
    def test_prompt_input_optional_fields(self):
        """Test PromptInput with optional fields."""
        # Test with minimal parameters
        prompt_input = PromptInput()
        assert prompt_input.table_name is None
        assert prompt_input.context is None
        assert prompt_input.prompt_name is None
    
    def test_prompt_result_creation(self):
        """Test PromptResult model creation."""
        suggestions = ["suggestion1", "suggestion2"]
        result = PromptResult(
            prompt="Test prompt",
            suggestions=suggestions
        )
        assert result.prompt == "Test prompt"
        assert result.suggestions == suggestions
    
    def test_prompt_result_empty_suggestions(self):
        """Test PromptResult with empty suggestions."""
        result = PromptResult(
            prompt="Test prompt",
            suggestions=[]
        )
        assert result.prompt == "Test prompt"
        assert result.suggestions == []


class TestDb2QueryHelper:
    """Test db2_query_helper function."""
    
    def test_basic_query_helper(self):
        """Test basic functionality of db2_query_helper."""
        args = PromptInput()
        result = db2_query_helper(None, args)
        
        assert isinstance(result, PromptResult)
        assert "DB2 database expert" in result.prompt
        assert "SELECT queries" in result.prompt
        assert len(result.suggestions) == 4
        assert "parameterized queries" in result.suggestions[0]
    
    def test_query_helper_with_table_name(self):
        """Test db2_query_helper with table name."""
        args = PromptInput(table_name="EMPLOYEES")
        result = db2_query_helper(None, args)
        
        assert "Focus on the table: EMPLOYEES" in result.prompt
        assert "DB2 database expert" in result.prompt
    
    def test_query_helper_with_context(self):
        """Test db2_query_helper with context."""
        args = PromptInput(context="Performance optimization needed")
        result = db2_query_helper(None, args)
        
        assert "Additional context: Performance optimization needed" in result.prompt
    
    def test_query_helper_with_all_parameters(self):
        """Test db2_query_helper with all parameters."""
        args = PromptInput(
            table_name="SALES_DATA",
            context="Monthly report generation"
        )
        result = db2_query_helper(None, args)
        
        assert "Focus on the table: SALES_DATA" in result.prompt
        assert "Additional context: Monthly report generation" in result.prompt
        assert "DB2 database expert" in result.prompt
    
    def test_query_helper_suggestions_content(self):
        """Test that query helper suggestions contain expected content."""
        args = PromptInput()
        result = db2_query_helper(None, args)
        
        expected_suggestions = [
            "Always use parameterized queries",
            "Consider using LIMIT for large result sets",
            "Use appropriate indexes for better performance",
            "Follow read-only access patterns"
        ]
        
        assert result.suggestions == expected_suggestions


class TestDb2SchemaAnalyzer:
    """Test db2_schema_analyzer function."""
    
    def test_basic_schema_analyzer(self):
        """Test basic functionality of db2_schema_analyzer."""
        args = PromptInput()
        result = db2_schema_analyzer(None, args)
        
        assert isinstance(result, PromptResult)
        assert "Analyze the DB2 database schema" in result.prompt
        assert "table relationships" in result.prompt
        assert len(result.suggestions) == 4
    
    def test_schema_analyzer_with_parameters(self):
        """Test schema analyzer with various parameters (should not affect output)."""
        args = PromptInput(
            table_name="TEST_TABLE",
            context="Schema analysis"
        )
        result = db2_schema_analyzer(None, args)
        
        # Schema analyzer doesn't use table_name or context in current implementation
        assert "Analyze the DB2 database schema" in result.prompt
        assert "TEST_TABLE" not in result.prompt  # Not used in current implementation
    
    def test_schema_analyzer_suggestions_content(self):
        """Test that schema analyzer suggestions contain expected content."""
        args = PromptInput()
        result = db2_schema_analyzer(None, args)
        
        expected_suggestions = [
            "Check foreign key relationships",
            "Analyze column data types and constraints",
            "Look for indexing opportunities",
            "Identify potential normalization issues"
        ]
        
        assert result.suggestions == expected_suggestions


class TestDynamicPromptEdgeCases:
    """Test edge cases for dynamic_prompt function."""
    
    @patch('src.db2_mcp_server.prompts.db2_prompts.dynamic_loader')
    def test_dynamic_prompt_with_context_from_args(self, mock_loader):
        """Test dynamic_prompt getting prompt_name from context."""
        mock_loader.get_prompt.return_value = {"template": "Test"}
        mock_loader.generate_prompt_text.return_value = "Generated"
        mock_loader.get_suggestions.return_value = ["Test suggestion"]
        
        # Test with prompt_name in context
        ctx = {'prompt_name': 'context_prompt'}
        args = PromptInput()
        
        result = dynamic_prompt(ctx, args)
        
        mock_loader.get_prompt.assert_called_with('context_prompt')
        assert result.prompt == "Generated"
    
    @patch('src.db2_mcp_server.prompts.db2_prompts.dynamic_loader')
    def test_dynamic_prompt_fallback_to_default(self, mock_loader):
        """Test dynamic_prompt fallback to default prompt name."""
        mock_loader.get_prompt.return_value = {"template": "Test"}
        mock_loader.generate_prompt_text.return_value = "Generated"
        mock_loader.get_suggestions.return_value = ["Test suggestion"]
        
        # Test without prompt_name
        ctx = {}
        args = PromptInput()
        
        result = dynamic_prompt(ctx, args)
        
        mock_loader.get_prompt.assert_called_with('default')
    
    @patch('src.db2_mcp_server.prompts.db2_prompts.dynamic_loader')
    def test_dynamic_prompt_with_available_prompts_fallback(self, mock_loader):
        """Test dynamic_prompt fallback message with available prompts."""
        mock_loader.get_prompt.return_value = None
        mock_loader.list_prompts.return_value = ['prompt1', 'prompt2']
        
        args = PromptInput(prompt_name="nonexistent")
        ctx = {}
        
        result = dynamic_prompt(ctx, args)
        
        assert "Prompt 'nonexistent' not found" in result.prompt
        assert "Available prompts: prompt1, prompt2" in result.prompt
    
    @patch('src.db2_mcp_server.prompts.db2_prompts.store_table_metadata_from_context')
    @patch('src.db2_mcp_server.prompts.db2_prompts.dynamic_loader')
    def test_dynamic_prompt_data_explainer_store_exception(self, mock_loader, mock_store):
        """Test dynamic_prompt handling exception in store_table_metadata_from_context."""
        mock_loader.get_prompt.return_value = {"template": "Test"}
        mock_loader.generate_prompt_text.return_value = "Generated"
        mock_loader.get_suggestions.return_value = ["Test suggestion"]
        mock_store.side_effect = Exception("Storage error")
        
        args = PromptInput(
            prompt_name="data_explainer",
            context="TABLE: users\nid: Primary key",
            table_name="users"
        )
        ctx = {}
        
        # Should not raise exception, just log warning
        result = dynamic_prompt(ctx, args)
        
        assert result.prompt == "Generated"
        mock_store.assert_called_once()
    
    @patch('src.db2_mcp_server.prompts.db2_prompts.get_stored_table_info')
    @patch('src.db2_mcp_server.prompts.db2_prompts.dynamic_loader')
    def test_dynamic_prompt_data_explainer_no_context_with_stored_info(self, mock_loader, mock_get_info):
        """Test data_explainer using stored metadata when no context provided."""
        mock_loader.get_prompt.return_value = {"template": "Test"}
        mock_loader.generate_prompt_text.return_value = "Generated"
        mock_loader.get_suggestions.return_value = ["Test suggestion"]
        mock_get_info.return_value = "Stored metadata info"
        
        args = PromptInput(
            prompt_name="data_explainer",
            table_name="users"
            # No context provided
        )
        ctx = {}
        
        result = dynamic_prompt(ctx, args)
        
        mock_get_info.assert_called_once_with("users")
        # Should call generate_prompt_text with enhanced context
        mock_loader.generate_prompt_text.assert_called_once()
        call_args = mock_loader.generate_prompt_text.call_args
        assert call_args[1]['context'] == "Stored metadata info"
    
    @patch('src.db2_mcp_server.prompts.db2_prompts.list_stored_tables')
    @patch('src.db2_mcp_server.prompts.db2_prompts.dynamic_loader')
    def test_dynamic_prompt_data_explainer_suggestions_with_stored_tables(self, mock_loader, mock_list_tables):
        """Test data_explainer suggestions include stored tables info."""
        mock_loader.get_prompt.return_value = {"template": "Test"}
        mock_loader.generate_prompt_text.return_value = "Generated"
        mock_loader.get_suggestions.return_value = ["Base suggestion"]
        mock_list_tables.return_value = ['table1', 'table2', 'table3']
        
        args = PromptInput(prompt_name="data_explainer")
        ctx = {}
        
        result = dynamic_prompt(ctx, args)
        
        # Should include stored tables info in suggestions
        stored_tables_suggestion = next(
            (s for s in result.suggestions if "Stored metadata available" in s),
            None
        )
        assert stored_tables_suggestion is not None
        assert "table1, table2, table3" in stored_tables_suggestion
    
    @patch('src.db2_mcp_server.prompts.db2_prompts.list_stored_tables')
    @patch('src.db2_mcp_server.prompts.db2_prompts.dynamic_loader')
    def test_dynamic_prompt_data_explainer_suggestions_many_tables(self, mock_loader, mock_list_tables):
        """Test data_explainer suggestions with many stored tables (truncation)."""
        mock_loader.get_prompt.return_value = {"template": "Test"}
        mock_loader.generate_prompt_text.return_value = "Generated"
        mock_loader.get_suggestions.return_value = ["Base suggestion"]
        # More than 5 tables to test truncation
        mock_list_tables.return_value = ['t1', 't2', 't3', 't4', 't5', 't6', 't7']
        
        args = PromptInput(prompt_name="data_explainer")
        ctx = {}
        
        result = dynamic_prompt(ctx, args)
        
        stored_tables_suggestion = next(
            (s for s in result.suggestions if "Stored metadata available" in s),
            None
        )
        assert stored_tables_suggestion is not None
        assert "..." in stored_tables_suggestion  # Should be truncated
        assert "t1, t2, t3, t4, t5..." in stored_tables_suggestion


class TestUtilityFunctions:
    """Test utility functions in db2_prompts module."""
    
    @patch('src.db2_mcp_server.prompts.db2_prompts.dynamic_loader')
    def test_get_available_dynamic_prompts(self, mock_loader):
        """Test get_available_dynamic_prompts function."""
        mock_loader.list_prompts.return_value = ['prompt1', 'prompt2']
        
        result = get_available_dynamic_prompts()
        
        assert result == ['prompt1', 'prompt2']
        mock_loader.list_prompts.assert_called_once()
    
    @patch('src.db2_mcp_server.prompts.db2_prompts.dynamic_loader')
    def test_reload_dynamic_prompts_success(self, mock_loader):
        """Test successful reload of dynamic prompts."""
        mock_loader.reload.return_value = None  # No exception
        
        result = reload_dynamic_prompts()
        
        assert result is True
        mock_loader.reload.assert_called_once()
    
    @patch('src.db2_mcp_server.prompts.db2_prompts.dynamic_loader')
    def test_reload_dynamic_prompts_failure(self, mock_loader):
        """Test failed reload of dynamic prompts."""
        mock_loader.reload.side_effect = Exception("Reload error")
        
        result = reload_dynamic_prompts()
        
        assert result is False
        mock_loader.reload.assert_called_once()
    
    @patch('src.db2_mcp_server.prompts.db2_prompts.dynamic_loader')
    def test_has_dynamic_prompts(self, mock_loader):
        """Test has_dynamic_prompts function."""
        mock_loader.has_prompts.return_value = True
        
        result = has_dynamic_prompts()
        
        assert result is True
        mock_loader.has_prompts.assert_called_once()


class TestStoreTableMetadataFromContextAdvanced:
    """Advanced tests for store_table_metadata_from_context function."""
    
    @patch('src.db2_mcp_server.prompts.db2_prompts.get_table_metadata_storage')
    @patch('src.db2_mcp_server.prompts.db2_prompts.parse_field_descriptions')
    @patch('src.db2_mcp_server.prompts.db2_prompts.extract_table_name_from_context')
    def test_store_metadata_with_provided_table_name(self, mock_extract, mock_parse, mock_get_storage):
        """Test store_table_metadata_from_context with provided table name."""
        mock_parse.return_value = {"id": "Primary key"}
        mock_storage = Mock()
        mock_storage.bulk_update_from_descriptions.return_value = True
        mock_get_storage.return_value = mock_storage
        
        context = "id: Primary key"
        table_name = "provided_table"
        
        result = store_table_metadata_from_context(context, table_name)
        
        assert result is True
        # Should not call extract_table_name_from_context when table_name is provided
        mock_extract.assert_not_called()
        mock_parse.assert_called_once_with(context)
        mock_storage.bulk_update_from_descriptions.assert_called_once_with(
            table_name="provided_table",
            field_descriptions={"id": "Primary key"}
        )
    
    @patch('src.db2_mcp_server.prompts.db2_prompts.get_table_metadata_storage')
    def test_store_metadata_exception_handling(self, mock_get_storage):
        """Test store_table_metadata_from_context exception handling."""
        mock_get_storage.side_effect = Exception("Storage error")
        
        context = "TABLE: users\nid: Primary key"
        
        result = store_table_metadata_from_context(context)
        
        assert result is False


class TestGetStoredTableInfoAdvanced:
    """Advanced tests for get_stored_table_info function."""
    
    @patch('src.db2_mcp_server.prompts.db2_prompts.get_table_metadata_storage')
    def test_get_stored_info_with_schema_name(self, mock_get_storage):
        """Test get_stored_table_info with schema name."""
        mock_metadata = TableMetadata(
            table_name="users",
            schema_name="public",
            fields=[FieldInfo(name="id", description="Primary key")]
        )
        mock_storage = Mock()
        mock_storage.get_table_metadata.return_value = mock_metadata
        mock_get_storage.return_value = mock_storage
        
        result = get_stored_table_info("users", "public")
        
        assert "TABLE: users" in result
        assert "id: Primary key" in result
        mock_storage.get_table_metadata.assert_called_once_with("users", "public")
    
    @patch('src.db2_mcp_server.prompts.db2_prompts.get_table_metadata_storage')
    def test_get_stored_info_fields_without_description(self, mock_get_storage):
        """Test get_stored_table_info with fields that have no description."""
        mock_metadata = TableMetadata(
            table_name="test_table",
            fields=[
                FieldInfo(name="id", description="Primary key"),
                FieldInfo(name="name", description=None),  # No description
                FieldInfo(name="email", description="Email address")
            ]
        )
        mock_storage = Mock()
        mock_storage.get_table_metadata.return_value = mock_metadata
        mock_get_storage.return_value = mock_storage
        
        result = get_stored_table_info("test_table")
        
        assert "TABLE: test_table" in result
        assert "id: Primary key" in result
        assert "email: Email address" in result
        # Field without description should not appear
        assert "name:" not in result
    
    @patch('src.db2_mcp_server.prompts.db2_prompts.get_table_metadata_storage')
    def test_get_stored_info_exception_handling(self, mock_get_storage):
        """Test get_stored_table_info exception handling."""
        mock_get_storage.side_effect = Exception("Storage error")
        
        result = get_stored_table_info("test_table")
        
        assert result is None


class TestListStoredTablesAdvanced:
    """Advanced tests for list_stored_tables function."""
    
    @patch('src.db2_mcp_server.prompts.db2_prompts.get_table_metadata_storage')
    def test_list_stored_tables_exception_handling(self, mock_get_storage):
        """Test list_stored_tables exception handling."""
        mock_get_storage.side_effect = Exception("Storage error")
        
        result = list_stored_tables()
        
        assert result == []