# Dynamic Prompt Loading

The DB2 MCP Server now supports dynamically loading prompts from JSON configuration files. This feature allows you to customize and extend the available prompts without modifying the source code.

## Configuration

To enable dynamic prompt loading, set the `PROMPTS_FILE` environment variable to point to your JSON configuration file:

```bash
export PROMPTS_FILE="/path/to/your/prompts_config.json"
```

## JSON Configuration Format

The JSON configuration file should follow this structure:

```json
{
  "version": "1.0",
  "global_suggestions": [
    "Global suggestion 1",
    "Global suggestion 2"
  ],
  "prompts": [
    {
      "name": "prompt_name",
      "description": "Description of what this prompt does",
      "base_prompt": "The main prompt text",
      "suggestions": [
        "Prompt-specific suggestion 1",
        "Prompt-specific suggestion 2"
      ],
      "context_template": "Template for context: {context}",
      "table_template": "Template for table: {table_name}",
      "metadata": {
        "category": "performance",
        "complexity": "advanced"
      }
    }
  ]
}
```

### Configuration Fields

#### Root Level
- `version` (string): Configuration format version (currently "1.0")
- `global_suggestions` (array): Suggestions that apply to all prompts
- `prompts` (array): List of prompt configurations

#### Prompt Configuration
- `name` (string, required): Unique identifier for the prompt
- `description` (string, required): Human-readable description
- `base_prompt` (string, required): The main prompt text
- `suggestions` (array, optional): Prompt-specific suggestions
- `context_template` (string, optional): Template for inserting context
- `table_template` (string, optional): Template for inserting table names
- `metadata` (object, optional): Additional metadata for the prompt

### Template Variables

Templates support the following variables:
- `{context}`: Replaced with the provided context string
- `{table_name}`: Replaced with the specified table name

## Usage

### Using Dynamic Prompts

Once configured, you can use dynamic prompts through the MCP interface:

```python
from db2_mcp_server.prompts.db2_prompts import dynamic_prompt

# Use performance analyzer with context
result = dynamic_prompt(
    prompt_name="performance_analyzer",
    context="Database experiencing slow query performance during peak hours",
    table_name="user_transactions"
)

# Use security auditor for table analysis
result = dynamic_prompt(
    prompt_name="security_auditor",
    table_name="sensitive_data"
)

# Use data explainer with field descriptions
result = dynamic_prompt(
    prompt_name="data_explainer",
    context="""
    TABLE: user
    name: username
    password: digested password
    last_login: timestamp of last login
    """,
    table_name="user"
)
```

### Available Functions

The following utility functions are available:

```python
from src.db2_mcp_server.prompts.db2_prompts import (
    get_available_dynamic_prompts,
    reload_dynamic_prompts,
    has_dynamic_prompts
)

# Get list of available dynamic prompts
prompts = get_available_dynamic_prompts()

# Check if any dynamic prompts are loaded
if has_dynamic_prompts():
    print("Dynamic prompts are available")

# Reload prompts from configuration file
reload_dynamic_prompts()
```

## Example Configuration

See `examples/prompts_config.json` for a complete example configuration with multiple prompt types:

- **performance_analyzer**: Analyze DB2 performance and suggest optimizations
- **security_auditor**: Audit database security and access controls
- **data_migration**: Assist with data migration planning
- **data_retriever**: Generate optimized SQL queries to retrieve data from specific tables
- **data_explainer**: Retrieve data from tables and provide detailed explanations of data structure and content
- **troubleshooter**: Diagnose and resolve database issues

## Data Explainer Prompt

The `data_explainer` prompt is specifically designed to help users understand and retrieve data from tables when provided with simple field descriptions. This prompt is ideal for:

### Use Cases
- **Data Discovery**: Understanding what data is stored in tables
- **Query Generation**: Creating SQL queries based on field descriptions
- **Data Documentation**: Explaining the purpose and meaning of table fields
- **Business Context**: Providing insights into how data can be used

### Input Format
Provide field descriptions in a simple format:
```
TABLE: table_name
field1: description of field1
field2: description of field2
field3: description of field3
```

### Example Usage
```python
# Example with user authentication table
result = dynamic_prompt(
    prompt_name="data_explainer",
    context="""
    TABLE: user
    name: username
    password: digested password
    last_login: timestamp of last login
    """,
    table_name="user"
)

# Example with product catalog
result = dynamic_prompt(
    prompt_name="data_explainer",
    context="""
    TABLE: product
    id: unique product identifier
    name: product name
    price: product price in USD
    category_id: foreign key to category table
    stock_quantity: available inventory count
    """,
    table_name="product"
)
```

### Generated Output
The data_explainer prompt will generate:
- **SQL Queries**: Optimized SELECT statements with meaningful aliases
- **Field Explanations**: Detailed descriptions of each field's purpose
- **Data Insights**: Suggestions for data analysis and filtering
- **Usage Examples**: Common query patterns for the table
- **Relationship Analysis**: Identification of foreign keys and relationships

## Error Handling

The dynamic prompt loader includes comprehensive error handling:

- **Missing environment variable**: Falls back to default prompts only
- **File not found**: Logs warning and continues with default prompts
- **Invalid JSON**: Logs error and continues with default prompts
- **Invalid configuration**: Validates against schema and logs errors
- **Missing prompt**: Returns helpful error message with available options

## Best Practices

1. **Validate your JSON**: Use a JSON validator before deploying
2. **Use descriptive names**: Choose clear, unique names for your prompts
3. **Include helpful suggestions**: Provide context-specific suggestions
4. **Test templates**: Verify that your templates work with various inputs
5. **Document metadata**: Use the metadata field to categorize and describe prompts
6. **Version control**: Keep your prompt configurations in version control
7. **Backup configurations**: Maintain backups of working configurations

## Troubleshooting

### Common Issues

1. **Prompts not loading**
   - Check that `PROMPTS_FILE` environment variable is set
   - Verify the file path exists and is readable
   - Check the application logs for error messages

2. **Invalid JSON errors**
   - Validate your JSON syntax using an online validator
   - Check for trailing commas or missing quotes
   - Ensure all required fields are present

3. **Template errors**
   - Verify template syntax uses correct variable names
   - Test templates with sample data
   - Check for typos in variable names

### Logging

The dynamic prompt loader logs important events:

- Info: Successful loading of prompts
- Warning: File not found or environment variable not set
- Error: JSON parsing errors or validation failures

Check your application logs for these messages to diagnose issues.

## Migration from Static Prompts

If you're migrating from static prompts:

1. Identify your existing prompt patterns
2. Create a JSON configuration with equivalent prompts
3. Test the configuration in a development environment
4. Set the `PROMPTS_FILE` environment variable
5. Restart the application to load the new configuration
6. Verify that prompts work as expected

## Performance Considerations

- Prompt configurations are loaded once at startup and cached in memory
- Use the `reload_dynamic_prompts()` function to refresh without restarting
- Large configuration files may impact startup time
- Consider splitting very large configurations into multiple files