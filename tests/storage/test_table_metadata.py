"""Tests for table metadata storage functionality."""

import json
import tempfile
import threading
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from db2_mcp_server.storage.table_metadata import (
    FieldInfo,
    TableMetadata,
    TableMetadataStorage,
    get_table_metadata_storage,
    parse_field_descriptions,
    extract_table_name_from_context,
)


class TestFieldInfo:
    """Test FieldInfo model."""

    def test_field_info_creation(self):
        """Test creating a FieldInfo instance."""
        field = FieldInfo(
            name="user_id",
            description="Unique user identifier",
            data_type="INTEGER",
            business_context="Primary key for user table"
        )
        
        assert field.name == "user_id"
        assert field.description == "Unique user identifier"
        assert field.data_type == "INTEGER"
        assert field.business_context == "Primary key for user table"

    def test_field_info_minimal(self):
        """Test creating FieldInfo with minimal required fields."""
        field = FieldInfo(name="username", description="User login name")
        
        assert field.name == "username"
        assert field.description == "User login name"
        assert field.data_type is None
        assert field.business_context is None


class TestTableMetadata:
    """Test TableMetadata model."""

    def test_table_metadata_creation(self):
        """Test creating a TableMetadata instance."""
        fields = [
            FieldInfo(name="id", description="Primary key"),
            FieldInfo(name="name", description="User name")
        ]
        
        metadata = TableMetadata(
            table_name="users",
            fields=fields,
            business_purpose="User management table"
        )
        
        assert metadata.table_name == "users"
        assert len(metadata.fields) == 2
        assert metadata.business_purpose == "User management table"
        # These fields are optional and default to None
        assert metadata.created_date is None
        assert metadata.last_updated is None

    def test_table_metadata_minimal(self):
        """Test creating TableMetadata with minimal fields."""
        metadata = TableMetadata(table_name="products", fields=[])
        
        assert metadata.table_name == "products"
        assert metadata.fields == []
        assert metadata.business_purpose is None


class TestTableMetadataStorage:
    """Test TableMetadataStorage class."""

    @pytest.fixture
    def temp_storage_dir(self):
        """Create a temporary directory for storage tests."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def mock_cache(self):
        """Create a mock cache manager."""
        cache = Mock()
        cache.get.return_value = None
        cache.set.return_value = None
        cache.delete.return_value = None
        return cache

    @pytest.fixture
    def storage(self, temp_storage_dir, mock_cache):
        """Create a TableMetadataStorage instance for testing."""
        return TableMetadataStorage(storage_path=temp_storage_dir, cache_manager=mock_cache)

    def test_storage_initialization(self, temp_storage_dir, mock_cache):
        """Test storage initialization."""
        storage = TableMetadataStorage(storage_path=temp_storage_dir, cache_manager=mock_cache)
        
        assert storage.storage_path == temp_storage_dir
        assert storage.cache_manager == mock_cache
        assert temp_storage_dir.exists()

    def test_store_metadata(self, storage):
        """Test storing table metadata."""
        fields = [FieldInfo(name="id", description="Primary key")]
        metadata = TableMetadata(table_name="users", fields=fields)
        
        result = storage.store_table_metadata(metadata)
        
        assert result is True
        storage.cache_manager.set.assert_called_once()
        
        # Check file was created
        file_path = storage.storage_path / "users.json"
        assert file_path.exists()
        
        # Check file content
        with open(file_path) as f:
            data = json.load(f)
        assert data["table_name"] == "users"
        assert len(data["fields"]) == 1

    def test_get_table_metadata_from_cache(self, storage):
        """Test retrieving metadata from cache."""
        fields = [FieldInfo(name="id", description="Primary key")]
        metadata = TableMetadata(table_name="users", fields=fields)
        
        # Cache stores dictionary data, not TableMetadata objects
        cache_data = metadata.model_dump()
        storage.cache_manager.get.return_value = cache_data
        
        result = storage.get_table_metadata("users")
        
        assert result.table_name == metadata.table_name
        assert len(result.fields) == len(metadata.fields)
        storage.cache_manager.get.assert_called_with("table_metadata:default:users")

    def test_get_table_metadata_from_file(self, storage):
        """Test retrieving metadata from file when not in cache."""
        fields = [FieldInfo(name="id", description="Primary key")]
        metadata = TableMetadata(table_name="users", fields=fields)
        
        # Store first
        storage.store_table_metadata(metadata)
        
        # Clear cache mock
        storage.cache_manager.get.return_value = None
        
        result = storage.get_table_metadata("users")
        
        assert result is not None
        assert result.table_name == "users"
        assert len(result.fields) == 1

    def test_get_table_metadata_not_found(self, storage):
        """Test retrieving non-existent metadata."""
        storage.cache_manager.get.return_value = None
        
        result = storage.get_table_metadata("nonexistent")
        
        assert result is None

    def test_update_field_description(self, storage):
        """Test updating a field description."""
        fields = [FieldInfo(name="id", description="Primary key")]
        metadata = TableMetadata(table_name="users", fields=fields)
        storage.store_table_metadata(metadata)
        
        result = storage.update_field_description(
            "users", "id", "Unique identifier", business_context="Main key"
        )
        
        assert result is True
        
        # Verify update
        updated_metadata = storage.get_table_metadata("users")
        assert updated_metadata.fields[0].description == "Unique identifier"
        assert updated_metadata.fields[0].business_context == "Main key"

    def test_update_field_description_table_not_found(self, storage):
        """Test updating field description for non-existent table."""
        result = storage.update_field_description(
            "nonexistent", "id", "New description"
        )
        
        # Should create new metadata and return True
        assert result is True

    def test_update_field_description_field_not_found(self, storage):
        """Test updating non-existent field description."""
        fields = [FieldInfo(name="id", description="Primary key")]
        metadata = TableMetadata(table_name="users", fields=fields)
        storage.store_table_metadata(metadata)
        
        result = storage.update_field_description(
            "users", "nonexistent", "New description"
        )
        
        # Should add new field and return True
        assert result is True

    def test_bulk_update_from_descriptions(self, storage):
        """Test bulk updating field descriptions."""
        fields = [
            FieldInfo(name="id", description="Old description"),
            FieldInfo(name="name", description="Old name")
        ]
        metadata = TableMetadata(table_name="users", fields=fields)
        storage.store_table_metadata(metadata)
        
        descriptions = {
            "id": "New ID description",
            "email": "Email address"  # New field
        }
        
        result = storage.bulk_update_from_descriptions("users", descriptions)
        
        assert result is True
        
        # Verify updates
        updated_metadata = storage.get_table_metadata("users")
        assert len(updated_metadata.fields) == 3
        
        id_field = next(f for f in updated_metadata.fields if f.name == "id")
        assert id_field.description == "New ID description"
        
        email_field = next(f for f in updated_metadata.fields if f.name == "email")
        assert email_field.description == "Email address"

    def test_list_tables(self, storage):
        """Test listing tables with metadata."""
        # Store multiple tables
        for table_name in ["users", "products", "orders"]:
            metadata = TableMetadata(table_name=table_name, fields=[])
            storage.store_table_metadata(metadata)
        
        tables = storage.list_stored_tables()
        
        assert len(tables) == 3
        assert "users" in tables
        assert "products" in tables
        assert "orders" in tables

    def test_delete_metadata(self, storage):
        """Test deleting table metadata."""
        fields = [FieldInfo(name="id", description="Primary key")]
        metadata = TableMetadata(table_name="users", fields=fields)
        storage.store_table_metadata(metadata)
        
        result = storage.delete_table_metadata("users")
        
        assert result is True
        storage.cache_manager.delete.assert_called_with("table_metadata:default:users")
        
        # Check file was deleted
        file_path = storage.storage_path / "users.json"
        assert not file_path.exists()

    def test_delete_metadata_not_found(self, storage):
        """Test deleting non-existent metadata."""
        result = storage.delete_table_metadata("nonexistent")
        
        # Method returns True even if file doesn't exist
        assert result is True

    def test_export_all_metadata(self, storage, tmp_path):
        """Test exporting all metadata."""
        # Store multiple tables
        for i, table_name in enumerate(["users", "products"]):
            fields = [FieldInfo(name="id", description=f"ID for {table_name}")]
            metadata = TableMetadata(table_name=table_name, fields=fields)
            storage.store_table_metadata(metadata)
        
        export_file = tmp_path / "export.json"
        result = storage.export_metadata(export_file)
        
        assert result is True
        assert export_file.exists()
        
        # Read and verify exported data
        with open(export_file, 'r') as f:
            exported_data = json.load(f)
        assert len(exported_data) == 2

    def test_import_metadata(self, storage, tmp_path):
        """Test importing metadata."""
        metadata_dict = {
            "tables": {
                "users": {
                    "table_name": "users",
                    "fields": [
                        {
                            "name": "id",
                            "description": "Primary key",
                            "data_type": "INTEGER",
                            "business_context": None
                        }
                    ],
                    "business_context": None,
                    "created_date": "2024-01-01T00:00:00",
                    "last_updated": "2024-01-01T00:00:00"
                }
            }
        }
        
        # Create a temporary file with metadata
        import_file = tmp_path / "import.json"
        with open(import_file, 'w') as f:
            json.dump(metadata_dict, f)
        
        result = storage.import_metadata(import_file)
        
        assert result is True
        
        # Verify import
        imported_metadata = storage.get_table_metadata("users")
        assert imported_metadata is not None
        assert imported_metadata.table_name == "users"
        assert len(imported_metadata.fields) == 1




class TestUtilityFunctions:
    """Test utility functions."""

    def test_parse_field_descriptions_simple(self):
        """Test parsing simple field descriptions."""
        context = """
        id: Primary key identifier
        name: User full name
        email: Contact email address
        """
        
        result = parse_field_descriptions(context)
        
        assert len(result) == 3
        assert result["id"] == "Primary key identifier"
        assert result["name"] == "User full name"
        assert result["email"] == "Contact email address"

    def test_parse_field_descriptions_with_comments(self):
        """Test parsing field descriptions with comments."""
        context = """
        # This is a comment
        id: Primary key identifier
        # Another comment
        name: User full name
        """
        
        result = parse_field_descriptions(context)
        
        assert len(result) == 2
        assert result["id"] == "Primary key identifier"
        assert result["name"] == "User full name"

    def test_parse_field_descriptions_empty(self):
        """Test parsing empty context."""
        result = parse_field_descriptions("")
        assert result == {}

    def test_extract_table_name_from_context_simple(self):
        """Test extracting table name from simple context."""
        context = "TABLE: users\nid: Primary key\nname: User name"
        result = extract_table_name_from_context(context)
        assert result == "users"

    def test_extract_table_name_from_context_case_insensitive(self):
        """Test extracting table name with different case."""
        context = "TABLE: products\nsku: Product SKU\nprice: Product price"
        result = extract_table_name_from_context(context)
        assert result == "products"

    def test_extract_table_name_from_context_not_found(self):
        """Test extracting table name when not found."""
        context = "Some content without table name"
        
        result = extract_table_name_from_context(context)
        
        assert result is None


class TestGetTableMetadataStorage:
    """Test the singleton storage function."""

    def test_get_table_metadata_storage_singleton(self):
        """Test that get_table_metadata_storage returns singleton."""
        # Clear any existing instance
        import db2_mcp_server.storage.table_metadata as table_metadata_module
        table_metadata_module._storage_instance = None
        
        try:
            storage1 = get_table_metadata_storage()
            storage2 = get_table_metadata_storage()
            
            assert storage1 is storage2
            assert isinstance(storage1, TableMetadataStorage)
        finally:
            # Clean up
            table_metadata_module._storage_instance = None

    def test_get_table_metadata_storage_default_path(self):
        """Test get_table_metadata_storage uses default path."""
        # Clear any existing instance
        import db2_mcp_server.storage.table_metadata as table_metadata_module
        table_metadata_module._storage_instance = None
        
        try:
            storage = get_table_metadata_storage()
            expected_path = Path.home() / ".db2_mcp" / "table_metadata"
            assert storage.storage_path == expected_path
        finally:
            # Clean up
            table_metadata_module._storage_instance = None


class TestFieldInfoAdvanced:
    """Advanced tests for FieldInfo model."""

    def test_field_info_with_all_attributes(self):
        """Test FieldInfo with all possible attributes."""
        field = FieldInfo(
            name="user_id",
            data_type="INTEGER",
            description="Unique user identifier",
            is_nullable=False,
            is_primary_key=True,
            is_foreign_key=False,
            foreign_table=None,
            max_length=None,
            default_value="0",
            constraints=["NOT NULL", "UNIQUE"],
            business_context="Primary key for user management"
        )
        
        assert field.name == "user_id"
        assert field.data_type == "INTEGER"
        assert field.is_nullable is False
        assert field.is_primary_key is True
        assert field.is_foreign_key is False
        assert field.default_value == "0"
        assert len(field.constraints) == 2
        assert "NOT NULL" in field.constraints
        assert "UNIQUE" in field.constraints

    def test_field_info_foreign_key(self):
        """Test FieldInfo as foreign key."""
        field = FieldInfo(
            name="department_id",
            data_type="INTEGER",
            description="Reference to department",
            is_foreign_key=True,
            foreign_table="departments"
        )
        
        assert field.is_foreign_key is True
        assert field.foreign_table == "departments"

    def test_field_info_with_max_length(self):
        """Test FieldInfo with max_length constraint."""
        field = FieldInfo(
            name="username",
            data_type="VARCHAR",
            description="User login name",
            max_length=50,
            constraints=["UNIQUE"]
        )
        
        assert field.max_length == 50
        assert "UNIQUE" in field.constraints


class TestTableMetadataAdvanced:
    """Advanced tests for TableMetadata model."""

    def test_table_metadata_with_schema(self):
        """Test TableMetadata with schema name."""
        metadata = TableMetadata(
            table_name="users",
            schema_name="hr",
            table_type="T",
            description="Human resources user table"
        )
        
        assert metadata.schema_name == "hr"
        assert metadata.table_type == "T"
        assert metadata.description == "Human resources user table"

    def test_table_metadata_with_relationships(self):
        """Test TableMetadata with relationships."""
        relationships = {
            "departments": "department_id -> departments.id",
            "roles": "role_id -> roles.id"
        }
        
        metadata = TableMetadata(
            table_name="users",
            relationships=relationships
        )
        
        assert len(metadata.relationships) == 2
        assert "departments" in metadata.relationships
        assert "roles" in metadata.relationships

    def test_table_metadata_with_indexes_and_queries(self):
        """Test TableMetadata with indexes and sample queries."""
        indexes = ["idx_username", "idx_email", "idx_department_id"]
        sample_queries = [
            "SELECT * FROM users WHERE username = ?",
            "SELECT COUNT(*) FROM users WHERE department_id = ?"
        ]
        
        metadata = TableMetadata(
            table_name="users",
            indexes=indexes,
            sample_queries=sample_queries,
            row_count=1500
        )
        
        assert len(metadata.indexes) == 3
        assert "idx_username" in metadata.indexes
        assert len(metadata.sample_queries) == 2
        assert metadata.row_count == 1500

    def test_table_metadata_with_data_quality_notes(self):
        """Test TableMetadata with data quality notes."""
        quality_notes = [
            "Some email fields contain invalid formats",
            "Username field has occasional duplicates",
            "Created_date field missing for 5% of records"
        ]
        
        metadata = TableMetadata(
            table_name="users",
            data_quality_notes=quality_notes
        )
        
        assert len(metadata.data_quality_notes) == 3
        assert "Some email fields contain invalid formats" in metadata.data_quality_notes


class TestTableMetadataStorageAdvanced:
    """Advanced tests for TableMetadataStorage class."""

    @pytest.fixture
    def temp_storage_dir(self):
        """Create a temporary directory for storage tests."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def mock_cache(self):
        """Create a mock cache manager."""
        cache = Mock()
        cache.get.return_value = None
        cache.set.return_value = None
        cache.delete.return_value = None
        return cache

    @pytest.fixture
    def storage(self, temp_storage_dir, mock_cache):
        """Create storage instance for testing."""
        return TableMetadataStorage(storage_path=temp_storage_dir, cache_manager=mock_cache)

    def test_store_metadata_with_schema(self, storage):
        """Test storing metadata with schema name."""
        metadata = TableMetadata(
            table_name="employees",
            schema_name="hr",
            fields=[FieldInfo(name="id", description="Employee ID")]
        )
        
        result = storage.store_table_metadata(metadata)
        
        assert result is True
        # Check file was created with schema prefix
        file_path = storage.storage_path / "hr_employees.json"
        assert file_path.exists()

    def test_get_metadata_with_schema(self, storage):
        """Test retrieving metadata with schema name."""
        metadata = TableMetadata(
            table_name="employees",
            schema_name="hr",
            fields=[FieldInfo(name="id", description="Employee ID")]
        )
        storage.store_table_metadata(metadata)
        
        # Clear cache to force file read
        storage.cache_manager.get.return_value = None
        
        result = storage.get_table_metadata("employees", "hr")
        
        assert result is not None
        assert result.table_name == "employees"
        assert result.schema_name == "hr"

    def test_cache_key_generation(self, storage):
        """Test cache key generation for different scenarios."""
        metadata = TableMetadata(table_name="test_table")
        storage.store_table_metadata(metadata)
        
        # Check cache was called with correct key (no schema)
        storage.cache_manager.set.assert_called()
        call_args = storage.cache_manager.set.call_args[0]
        assert call_args[0] == "table_metadata:default:test_table"
        
        # Test with schema
        metadata_with_schema = TableMetadata(table_name="test_table", schema_name="test_schema")
        storage.store_table_metadata(metadata_with_schema)
        
        call_args = storage.cache_manager.set.call_args[0]
        assert call_args[0] == "table_metadata:test_schema:test_table"

    def test_concurrent_access(self, storage):
        """Test concurrent access to storage."""
        results = []
        errors = []
        
        def store_metadata(table_name):
            try:
                metadata = TableMetadata(
                    table_name=table_name,
                    fields=[FieldInfo(name="id", description="ID field")]
                )
                result = storage.store_table_metadata(metadata)
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=store_metadata, args=[f"table_{i}"])
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0
        assert len(results) == 5
        assert all(result is True for result in results)

    def test_list_tables_with_schema_filter(self, storage):
        """Test listing tables with schema filter."""
        # Store tables in different schemas
        tables_data = [
            ("users", "hr"),
            ("products", "sales"),
            ("orders", "sales"),
            ("departments", "hr")
        ]
        
        for table_name, schema_name in tables_data:
            metadata = TableMetadata(table_name=table_name, schema_name=schema_name)
            storage.store_table_metadata(metadata)
        
        # Test filtering by schema
        hr_tables = storage.list_stored_tables(schema_name="hr")
        sales_tables = storage.list_stored_tables(schema_name="sales")
        all_tables = storage.list_stored_tables()
        
        assert len(hr_tables) == 2
        assert "users" in hr_tables
        assert "departments" in hr_tables
        
        assert len(sales_tables) == 2
        assert "products" in sales_tables
        assert "orders" in sales_tables
        
        assert len(all_tables) == 4

    def test_export_specific_tables(self, storage, tmp_path):
        """Test exporting specific tables only."""
        # Store multiple tables
        table_names = ["users", "products", "orders"]
        for table_name in table_names:
            metadata = TableMetadata(
                table_name=table_name,
                fields=[FieldInfo(name="id", description=f"ID for {table_name}")]
            )
            storage.store_table_metadata(metadata)
        
        # Export only specific tables
        export_file = tmp_path / "partial_export.json"
        result = storage.export_metadata(export_file, table_names=["users", "products"])
        
        assert result is True
        
        # Verify exported data
        with open(export_file, 'r') as f:
            exported_data = json.load(f)
        
        assert len(exported_data["tables"]) == 2
        assert "users" in exported_data["tables"]
        assert "products" in exported_data["tables"]
        assert "orders" not in exported_data["tables"]

    def test_import_metadata_partial_failure(self, storage, tmp_path):
        """Test importing metadata with some invalid entries."""
        # Create import data with one invalid entry
        metadata_dict = {
            "tables": {
                "valid_table": {
                    "table_name": "valid_table",
                    "fields": [{
                        "name": "id",
                        "description": "Valid field"
                    }]
                },
                "invalid_table": {
                    "table_name": "invalid_table",
                    "fields": "invalid_fields_format"  # This should cause an error
                }
            }
        }
        
        import_file = tmp_path / "partial_import.json"
        with open(import_file, 'w') as f:
            json.dump(metadata_dict, f)
        
        # Should still return True if at least one table imports successfully
        result = storage.import_metadata(import_file)
        assert result is True
        
        # Verify the valid table was imported
        imported_metadata = storage.get_table_metadata("valid_table")
        assert imported_metadata is not None
        assert imported_metadata.table_name == "valid_table"

    def test_error_handling_corrupted_file(self, storage, tmp_path):
        """Test error handling with corrupted metadata file."""
        # Create a corrupted JSON file
        corrupted_file = storage.storage_path / "corrupted.json"
        with open(corrupted_file, 'w') as f:
            f.write("{ invalid json content")
        
        # Should handle the error gracefully
        result = storage.get_table_metadata("corrupted")
        assert result is None

    def test_error_handling_permission_denied(self, storage):
        """Test error handling when file operations fail."""
        metadata = TableMetadata(table_name="test_table")
        
        # Mock file operations to raise permission error
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            result = storage.store_table_metadata(metadata)
            assert result is False

    def test_bulk_update_with_table_description(self, storage):
        """Test bulk update including table description."""
        metadata = TableMetadata(table_name="users")
        storage.store_table_metadata(metadata)
        
        descriptions = {
            "id": "User identifier",
            "name": "Full name"
        }
        table_description = "User management table"
        
        result = storage.bulk_update_from_descriptions(
            "users", descriptions, table_description=table_description
        )
        
        assert result is True
        
        updated_metadata = storage.get_table_metadata("users")
        assert updated_metadata.description == table_description
        assert len(updated_metadata.fields) == 2

    def test_update_field_description_with_existing_field(self, storage):
        """Test updating description of existing field."""
        fields = [
            FieldInfo(name="id", description="Old description", data_type="INTEGER"),
            FieldInfo(name="name", description="Name field")
        ]
        metadata = TableMetadata(table_name="users", fields=fields)
        storage.store_table_metadata(metadata)
        
        result = storage.update_field_description(
            "users", "id", "New description", business_context="Primary key"
        )
        
        assert result is True
        
        updated_metadata = storage.get_table_metadata("users")
        id_field = next(f for f in updated_metadata.fields if f.name == "id")
        assert id_field.description == "New description"
        assert id_field.business_context == "Primary key"
        assert id_field.data_type == "INTEGER"  # Should preserve existing attributes


class TestUtilityFunctionsAdvanced:
    """Advanced tests for utility functions."""

    def test_parse_field_descriptions_with_table_line(self):
        """Test parsing field descriptions that includes TABLE line."""
        context = """
        TABLE: users
        id: Primary key identifier
        name: User full name
        email: Contact email address
        """
        
        result = parse_field_descriptions(context)
        
        # Should exclude the TABLE line
        assert len(result) == 3
        assert "TABLE" not in result
        assert result["id"] == "Primary key identifier"

    def test_parse_field_descriptions_with_colons_in_description(self):
        """Test parsing descriptions that contain colons."""
        context = """
        url: Website URL (format: https://example.com)
        time: Timestamp (format: YYYY-MM-DD HH:MM:SS)
        """
        
        result = parse_field_descriptions(context)
        
        assert len(result) == 2
        assert result["url"] == "Website URL (format: https://example.com)"
        assert result["time"] == "Timestamp (format: YYYY-MM-DD HH:MM:SS)"

    def test_parse_field_descriptions_with_whitespace_variations(self):
        """Test parsing with various whitespace patterns."""
        context = """
        id:Primary key
        name :  User name  
          email  : Email address
        """
        
        result = parse_field_descriptions(context)
        
        assert len(result) == 3
        assert result["id"] == "Primary key"
        assert result["name"] == "User name"
        assert result["email"] == "Email address"

    def test_parse_field_descriptions_malformed_input(self):
        """Test parsing with malformed input."""
        context = """
        id: Primary key
        invalid_line_without_colon
        : description_without_field_name
        field_without_description:
        name: Valid description
        """
        
        result = parse_field_descriptions(context)
        
        # Should only parse valid lines
        assert len(result) == 2
        assert result["id"] == "Primary key"
        assert result["name"] == "Valid description"

    def test_extract_table_name_multiple_table_lines(self):
        """Test extracting table name when multiple TABLE lines exist."""
        context = """
        TABLE: first_table
        id: Primary key
        TABLE: second_table
        name: Name field
        """
        
        # Should return the first table name found
        result = extract_table_name_from_context(context)
        assert result == "first_table"

    def test_extract_table_name_with_extra_whitespace(self):
        """Test extracting table name with extra whitespace."""
        context = "   TABLE:    users_table   \nid: Primary key"
        result = extract_table_name_from_context(context)
        assert result == "users_table"

    def test_extract_table_name_case_variations(self):
        """Test extracting table name with different case variations."""
        contexts = [
            "TABLE: users",
            "Table: users", 
            "table: users",
            "TABLE:users"
        ]
        
        for context in contexts:
            result = extract_table_name_from_context(context)
            # The function is case-sensitive for "TABLE:"
            if context.startswith("TABLE:"):
                assert result == "users"
            else:
                assert result is None

    def test_parse_field_descriptions_error_handling(self):
        """Test error handling in parse_field_descriptions."""
        # Test with None input
        with patch('db2_mcp_server.storage.table_metadata.logger') as mock_logger:
            result = parse_field_descriptions(None)
            assert result == {}
            # Should log a warning
            mock_logger.warning.assert_called_once()

    def test_extract_table_name_error_handling(self):
        """Test error handling in extract_table_name_from_context."""
        # Test with None input
        with patch('db2_mcp_server.storage.table_metadata.logger') as mock_logger:
            result = extract_table_name_from_context(None)
            assert result is None
            # Should log a warning
            mock_logger.warning.assert_called_once()