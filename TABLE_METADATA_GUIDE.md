# Table Metadata Storage Guide for Data Explainer

This guide explains how to store and manage table information for use with the `data_explainer` prompt in the DB2 MCP Server.

## Overview

The `data_explainer` prompt can automatically store and retrieve table metadata (field descriptions, business context) to provide better analysis and insights. This metadata is stored persistently and cached for performance.

## Storage Methods

### 1. Automatic Storage (Recommended)

When you use the `data_explainer` prompt with field descriptions in the context, the metadata is automatically stored:

```python
from db2_mcp_server.prompts.db2_prompts import dynamic_prompt

# Context with field descriptions
context = """
Table: users
Fields:
- id: Unique user identifier (primary key)
- username: Login name for authentication
- email: User's email address for notifications
- created_at: Account creation timestamp
- last_login: Last successful login time
"""

# This automatically stores the metadata
result = dynamic_prompt("data_explainer", context=context, table_name="users")
```

### 2. Manual Storage via CLI

Use the CLI utility for batch operations and management:

#### Create a sample file template:
```bash
python examples/table_metadata_cli.py sample --output my_table.txt
```

#### Edit the file with your field descriptions:
```
id: Unique identifier for the record
name: Human-readable name or title
description: Detailed description of the item
created_at: Timestamp when record was created
updated_at: Timestamp when record was last modified
status: Current status (active, inactive, pending)
user_id: Foreign key reference to users table
category: Classification or grouping of the item
```

#### Store the metadata:
```bash
python examples/table_metadata_cli.py store --file my_table.txt
```

#### Interactive storage:
```bash
python examples/table_metadata_cli.py store --table users --interactive
```

### 3. Programmatic Storage

Use the storage API directly in your code:

```python
from db2_mcp_server.storage import get_table_metadata_storage, FieldInfo, TableMetadata

# Get storage instance
storage = get_table_metadata_storage()

# Create field information
fields = [
    FieldInfo(name="id", description="Unique user identifier", data_type="INTEGER"),
    FieldInfo(name="username", description="Login name", data_type="VARCHAR(50)"),
    FieldInfo(name="email", description="Email address", data_type="VARCHAR(255)")
]

# Store metadata
metadata = TableMetadata(
    table_name="users",
    fields=fields,
    business_context="User authentication and profile management"
)
storage.store_metadata(metadata)
```

## Management Operations

### List stored tables:
```bash
python examples/table_metadata_cli.py list
```

### Show table metadata:
```bash
python examples/table_metadata_cli.py show --table users
```

### Delete table metadata:
```bash
python examples/table_metadata_cli.py delete --table users
```

### Export metadata:
```bash
python examples/table_metadata_cli.py export --output backup.json
```

### Import metadata:
```bash
python examples/table_metadata_cli.py import --input backup.json
```

## File Format for Bulk Storage

When using files for storage, use this format:

```
# Comments start with #
# Table name is inferred from filename or can be specified

field_name: Field description
another_field: Another field description
status: Current status (active, inactive, pending)
created_at: Timestamp when record was created
```

## Storage Location

Metadata is stored in:
- **Location**: `~/.db2_mcp/table_metadata/`
- **Format**: JSON files (one per table)
- **Caching**: In-memory cache with 10-minute TTL

## Integration with Data Explainer

Once metadata is stored, the `data_explainer` prompt automatically:

1. **Retrieves stored metadata** for the specified table
2. **Enhances context** with field descriptions and business context
3. **Provides better analysis** based on stored information
4. **Suggests related operations** using the metadata

### Example with stored metadata:

```python
# After storing metadata for 'users' table
result = dynamic_prompt("data_explainer", table_name="users")
# The prompt automatically includes stored field descriptions
```

## Best Practices

1. **Use descriptive field names**: Include business meaning, not just technical details
2. **Add business context**: Explain how the table fits into business processes
3. **Include data types**: Specify column types when relevant
4. **Document relationships**: Mention foreign keys and table relationships
5. **Keep descriptions current**: Update metadata when schema changes
6. **Use consistent naming**: Follow naming conventions across tables

## Example Workflow

1. **Initial Setup**:
   ```bash
   # Create sample file
   python examples/table_metadata_cli.py sample --output users_table.txt
   
   # Edit file with your field descriptions
   # Store metadata
   python examples/table_metadata_cli.py store --file users_table.txt
   ```

2. **Use with Data Explainer**:
   ```python
   # Now the data_explainer has rich context
   result = dynamic_prompt("data_explainer", table_name="users")
   ```

3. **Manage and Maintain**:
   ```bash
   # List all tables
   python examples/table_metadata_cli.py list
   
   # Update specific table
   python examples/table_metadata_cli.py store --table users --interactive
   
   # Backup metadata
   python examples/table_metadata_cli.py export --output metadata_backup.json
   ```

## Troubleshooting

### Common Issues:

1. **Metadata not found**: Ensure table name matches exactly
2. **Permission errors**: Check write permissions to `~/.db2_mcp/`
3. **Cache issues**: Metadata is cached for 10 minutes; restart if needed
4. **File format errors**: Ensure proper `field: description` format

### Debug Commands:

```bash
# Check if metadata exists
python examples/table_metadata_cli.py show --table your_table

# List all stored tables
python examples/table_metadata_cli.py list

# Verify file format
cat your_table.txt
```

## Advanced Features

### Bulk Operations:
```python
# Update multiple fields at once
storage.bulk_update_from_descriptions("users", {
    "id": "Primary key identifier",
    "status": "Account status with workflow tracking"
})
```

### Export/Import:
```python
# Export all metadata
metadata_dict = storage.export_all_metadata()

# Import from dictionary
storage.import_metadata(metadata_dict)
```

### Custom Business Context:
```python
# Add business context
storage.update_business_context("users", 
    "Critical table for user authentication and profile management")
```

This comprehensive metadata system ensures that your `data_explainer` prompt has rich context to provide meaningful insights about your database tables.