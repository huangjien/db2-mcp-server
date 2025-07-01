#!/usr/bin/env python3
"""
Table Metadata Storage for Data Explainer

This module provides functionality to store, retrieve, and manage table metadata
for the data explainer prompt. It supports both in-memory caching and persistent
storage of table schema information, field descriptions, and analysis results.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
import threading
from ..cache import CacheManager

logger = logging.getLogger(__name__)

class FieldInfo(BaseModel):
    """Information about a table field/column."""
    name: str = Field(..., description="Field name")
    data_type: Optional[str] = Field(None, description="DB2 data type")
    description: Optional[str] = Field(None, description="Human-readable description")
    is_nullable: Optional[bool] = Field(None, description="Whether field can be NULL")
    is_primary_key: Optional[bool] = Field(False, description="Whether field is primary key")
    is_foreign_key: Optional[bool] = Field(False, description="Whether field is foreign key")
    foreign_table: Optional[str] = Field(None, description="Referenced table if foreign key")
    max_length: Optional[int] = Field(None, description="Maximum field length")
    default_value: Optional[str] = Field(None, description="Default value")
    constraints: List[str] = Field(default=[], description="Field constraints")
    business_context: Optional[str] = Field(None, description="Business meaning and usage")

class TableMetadata(BaseModel):
    """Complete metadata for a database table."""
    table_name: str = Field(..., description="Table name")
    schema_name: Optional[str] = Field(None, description="Schema name")
    table_type: Optional[str] = Field(None, description="Table type (T=Table, V=View, etc.)")
    description: Optional[str] = Field(None, description="Table description")
    fields: List[FieldInfo] = Field(default=[], description="Table fields/columns")
    relationships: Dict[str, str] = Field(default={}, description="Table relationships")
    indexes: List[str] = Field(default=[], description="Table indexes")
    row_count: Optional[int] = Field(None, description="Approximate row count")
    created_date: Optional[datetime] = Field(None, description="Table creation date")
    last_updated: Optional[datetime] = Field(None, description="Last update timestamp")
    business_purpose: Optional[str] = Field(None, description="Business purpose of the table")
    data_quality_notes: List[str] = Field(default=[], description="Data quality observations")
    sample_queries: List[str] = Field(default=[], description="Common query patterns")
    metadata_version: str = Field(default="1.0", description="Metadata schema version")
    
class TableMetadataStorage:
    """Storage manager for table metadata with caching and persistence."""
    
    def __init__(self, storage_path: Optional[Union[str, Path]] = None, cache_manager: Optional[CacheManager] = None):
        """Initialize table metadata storage.
        
        Args:
            storage_path: Path to store persistent metadata files
            cache_manager: Cache manager instance for in-memory caching
        """
        self.storage_path = Path(storage_path) if storage_path else Path.home() / ".db2_mcp" / "table_metadata"
        self.cache_manager = cache_manager or CacheManager()
        self._lock = threading.Lock()
        
        # Ensure storage directory exists
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized table metadata storage at {self.storage_path}")
    
    def store_table_metadata(self, metadata: TableMetadata, cache_ttl: int = 3600) -> bool:
        """Store table metadata with caching and persistence.
        
        Args:
            metadata: Table metadata to store
            cache_ttl: Cache time-to-live in seconds (default: 1 hour)
            
        Returns:
            bool: True if stored successfully
        """
        try:
            with self._lock:
                # Update timestamp
                metadata.last_updated = datetime.now()
                
                # Cache the metadata
                cache_key = f"table_metadata:{metadata.schema_name or 'default'}:{metadata.table_name}"
                self.cache_manager.set(cache_key, metadata.dict(), ttl=cache_ttl)
                
                # Persist to file
                file_path = self._get_metadata_file_path(metadata.table_name, metadata.schema_name)
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata.dict(), f, indent=2, default=str)
                
                logger.info(f"Stored metadata for table {metadata.table_name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to store metadata for table {metadata.table_name}: {e}")
            return False
    
    def get_table_metadata(self, table_name: str, schema_name: Optional[str] = None) -> Optional[TableMetadata]:
        """Retrieve table metadata from cache or storage.
        
        Args:
            table_name: Name of the table
            schema_name: Schema name (optional)
            
        Returns:
            TableMetadata or None if not found
        """
        try:
            # Try cache first
            cache_key = f"table_metadata:{schema_name or 'default'}:{table_name}"
            cached_data = self.cache_manager.get(cache_key)
            
            if cached_data:
                return TableMetadata(**cached_data)
            
            # Try persistent storage
            file_path = self._get_metadata_file_path(table_name, schema_name)
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    metadata = TableMetadata(**data)
                    
                    # Re-cache the data
                    self.cache_manager.set(cache_key, data, ttl=3600)
                    return metadata
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve metadata for table {table_name}: {e}")
            return None
    
    def update_field_description(self, table_name: str, field_name: str, description: str, 
                               schema_name: Optional[str] = None, business_context: Optional[str] = None) -> bool:
        """Update field description and business context.
        
        Args:
            table_name: Name of the table
            field_name: Name of the field
            description: Field description
            schema_name: Schema name (optional)
            business_context: Business context (optional)
            
        Returns:
            bool: True if updated successfully
        """
        try:
            metadata = self.get_table_metadata(table_name, schema_name)
            if not metadata:
                # Create new metadata if it doesn't exist
                metadata = TableMetadata(table_name=table_name, schema_name=schema_name)
            
            # Find and update the field
            field_found = False
            for field in metadata.fields:
                if field.name == field_name:
                    field.description = description
                    if business_context:
                        field.business_context = business_context
                    field_found = True
                    break
            
            # Add new field if not found
            if not field_found:
                new_field = FieldInfo(
                    name=field_name,
                    description=description,
                    business_context=business_context
                )
                metadata.fields.append(new_field)
            
            return self.store_table_metadata(metadata)
            
        except Exception as e:
            logger.error(f"Failed to update field description for {table_name}.{field_name}: {e}")
            return False
    
    def bulk_update_from_descriptions(self, table_name: str, field_descriptions: Dict[str, str], 
                                    schema_name: Optional[str] = None, table_description: Optional[str] = None) -> bool:
        """Bulk update table metadata from field descriptions.
        
        This is particularly useful for the data_explainer prompt when users provide
        field descriptions in the format: field_name: description
        
        Args:
            table_name: Name of the table
            field_descriptions: Dictionary of field_name -> description
            schema_name: Schema name (optional)
            table_description: Overall table description (optional)
            
        Returns:
            bool: True if updated successfully
        """
        try:
            metadata = self.get_table_metadata(table_name, schema_name)
            if not metadata:
                metadata = TableMetadata(table_name=table_name, schema_name=schema_name)
            
            if table_description:
                metadata.description = table_description
            
            # Update or add fields
            existing_fields = {field.name: field for field in metadata.fields}
            
            for field_name, description in field_descriptions.items():
                if field_name in existing_fields:
                    existing_fields[field_name].description = description
                else:
                    new_field = FieldInfo(name=field_name, description=description)
                    metadata.fields.append(new_field)
            
            return self.store_table_metadata(metadata)
            
        except Exception as e:
            logger.error(f"Failed to bulk update metadata for table {table_name}: {e}")
            return False
    
    def list_stored_tables(self, schema_name: Optional[str] = None) -> List[str]:
        """List all tables with stored metadata.
        
        Args:
            schema_name: Filter by schema name (optional)
            
        Returns:
            List of table names
        """
        try:
            tables = []
            pattern = "*.json"
            
            for file_path in self.storage_path.glob(pattern):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        table_schema = data.get('schema_name')
                        table_name = data.get('table_name')
                        
                        if schema_name is None or table_schema == schema_name:
                            tables.append(table_name)
                            
                except Exception as e:
                    logger.warning(f"Failed to read metadata file {file_path}: {e}")
                    continue
            
            return sorted(tables)
            
        except Exception as e:
            logger.error(f"Failed to list stored tables: {e}")
            return []
    
    def delete_table_metadata(self, table_name: str, schema_name: Optional[str] = None) -> bool:
        """Delete table metadata from cache and storage.
        
        Args:
            table_name: Name of the table
            schema_name: Schema name (optional)
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            with self._lock:
                # Remove from cache
                cache_key = f"table_metadata:{schema_name or 'default'}:{table_name}"
                self.cache_manager.delete(cache_key)
                
                # Remove from storage
                file_path = self._get_metadata_file_path(table_name, schema_name)
                if file_path.exists():
                    file_path.unlink()
                
                logger.info(f"Deleted metadata for table {table_name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete metadata for table {table_name}: {e}")
            return False
    
    def export_metadata(self, output_path: Union[str, Path], table_names: Optional[List[str]] = None) -> bool:
        """Export table metadata to a JSON file.
        
        Args:
            output_path: Path to export file
            table_names: List of table names to export (None for all)
            
        Returns:
            bool: True if exported successfully
        """
        try:
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "tables": {}
            }
            
            stored_tables = self.list_stored_tables()
            tables_to_export = table_names if table_names else stored_tables
            
            for table_name in tables_to_export:
                if table_name in stored_tables:
                    metadata = self.get_table_metadata(table_name)
                    if metadata:
                        export_data["tables"][table_name] = metadata.dict()
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            logger.info(f"Exported metadata for {len(export_data['tables'])} tables to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export metadata: {e}")
            return False
    
    def import_metadata(self, input_path: Union[str, Path]) -> bool:
        """Import table metadata from a JSON file.
        
        Args:
            input_path: Path to import file
            
        Returns:
            bool: True if imported successfully
        """
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            tables_data = import_data.get("tables", {})
            imported_count = 0
            
            for table_name, table_data in tables_data.items():
                try:
                    metadata = TableMetadata(**table_data)
                    if self.store_table_metadata(metadata):
                        imported_count += 1
                except Exception as e:
                    logger.warning(f"Failed to import metadata for table {table_name}: {e}")
                    continue
            
            logger.info(f"Imported metadata for {imported_count} tables from {input_path}")
            return imported_count > 0
            
        except Exception as e:
            logger.error(f"Failed to import metadata: {e}")
            return False
    
    def _get_metadata_file_path(self, table_name: str, schema_name: Optional[str] = None) -> Path:
        """Get the file path for storing table metadata.
        
        Args:
            table_name: Name of the table
            schema_name: Schema name (optional)
            
        Returns:
            Path to metadata file
        """
        if schema_name:
            filename = f"{schema_name}_{table_name}.json"
        else:
            filename = f"{table_name}.json"
        
        return self.storage_path / filename

# Global instance for easy access
_storage_instance: Optional[TableMetadataStorage] = None

def get_table_metadata_storage() -> TableMetadataStorage:
    """Get the global table metadata storage instance."""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = TableMetadataStorage()
    return _storage_instance

def parse_field_descriptions(context: str) -> Dict[str, str]:
    """Parse field descriptions from context text.
    
    Expected format:
    TABLE: table_name
    field1: description1
    field2: description2
    
    Args:
        context: Context text with field descriptions
        
    Returns:
        Dictionary of field_name -> description
    """
    field_descriptions = {}
    
    try:
        lines = context.strip().split('\n')
        for line in lines:
            line = line.strip()
            if ':' in line and not line.startswith('TABLE:'):
                parts = line.split(':', 1)
                if len(parts) == 2:
                    field_name = parts[0].strip()
                    description = parts[1].strip()
                    if field_name and description:
                        field_descriptions[field_name] = description
    
    except Exception as e:
        logger.warning(f"Failed to parse field descriptions: {e}")
    
    return field_descriptions

def extract_table_name_from_context(context: str) -> Optional[str]:
    """Extract table name from context text.
    
    Args:
        context: Context text
        
    Returns:
        Table name or None if not found
    """
    try:
        lines = context.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('TABLE:'):
                table_name = line.replace('TABLE:', '').strip()
                return table_name
    except Exception as e:
        logger.warning(f"Failed to extract table name from context: {e}")
    
    return None