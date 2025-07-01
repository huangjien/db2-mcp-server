from typing import List, Optional
from pydantic import BaseModel, Field
from fastmcp import FastMCP
from ..mcp_instance import mcp  # Import the shared mcp instance
from .dynamic_loader import dynamic_loader, DynamicPromptConfig
from ..storage import (
    get_table_metadata_storage,
    parse_field_descriptions,
    extract_table_name_from_context
)
import logging

logger = logging.getLogger(__name__)

class PromptInput(BaseModel):
    """Input for DB2 prompts."""
    context: Optional[str] = Field(None, description="Additional context for the prompt")
    table_name: Optional[str] = Field(None, description="Specific table name to focus on")
    prompt_name: Optional[str] = Field(None, description="Name of the dynamic prompt to use")

class PromptResult(BaseModel):
    """Result schema for prompts."""
    prompt: str = Field(..., description="Generated prompt text")
    suggestions: List[str] = Field(default=[], description="Additional suggestions")

@mcp.prompt(name="db2_query_helper")
def db2_query_helper(ctx, args: PromptInput) -> PromptResult:
    """Generate helpful prompts for DB2 query construction."""
    base_prompt = "You are a DB2 database expert. Help the user construct efficient and safe SELECT queries."
    
    if args.table_name:
        base_prompt += f" Focus on the table: {args.table_name}"
    
    if args.context:
        base_prompt += f" Additional context: {args.context}"
    
    suggestions = [
        "Always use parameterized queries",
        "Consider using LIMIT for large result sets",
        "Use appropriate indexes for better performance",
        "Follow read-only access patterns"
    ]
    
    return PromptResult(prompt=base_prompt, suggestions=suggestions)

@mcp.prompt(name="db2_schema_analyzer")
def db2_schema_analyzer(ctx, args: PromptInput) -> PromptResult:
    """Generate prompts for analyzing DB2 schema structures."""
    prompt = "Analyze the DB2 database schema and provide insights about table relationships, data types, and optimization opportunities."
    
    suggestions = [
        "Check foreign key relationships",
        "Analyze column data types and constraints",
        "Look for indexing opportunities",
        "Identify potential normalization issues"
    ]
    
    return PromptResult(prompt=prompt, suggestions=suggestions)

@mcp.prompt(name="dynamic_prompt")
def dynamic_prompt(ctx, args: PromptInput) -> PromptResult:
    """Generate prompts using dynamically loaded configurations from JSON file."""
    # Get prompt name from context or use a default
    prompt_name = getattr(args, 'prompt_name', None) or ctx.get('prompt_name', 'default')
    
    # Try to get dynamic prompt configuration
    prompt_config = dynamic_loader.get_prompt(prompt_name)
    
    if not prompt_config:
        # Fallback to a generic prompt if no dynamic config found
        available_prompts = dynamic_loader.list_prompts()
        if available_prompts:
            fallback_msg = f"Prompt '{prompt_name}' not found. Available prompts: {', '.join(available_prompts)}"
        else:
            fallback_msg = "No dynamic prompts loaded. Check PROMPTS_FILE environment variable."
        
        return PromptResult(
            prompt=f"Dynamic prompt loading failed. {fallback_msg}",
            suggestions=["Check PROMPTS_FILE environment variable", "Verify JSON file format"]
        )
    
    # Special handling for data_explainer prompt - store table metadata
    if prompt_name == 'data_explainer' and args.context:
        try:
            store_table_metadata_from_context(args.context, args.table_name)
        except Exception as e:
            logger.warning(f"Failed to store table metadata for data_explainer: {e}")
    
    # For data_explainer, try to enhance context with stored metadata if available
    enhanced_context = args.context
    if prompt_name == 'data_explainer' and args.table_name and not args.context:
        stored_info = get_stored_table_info(args.table_name)
        if stored_info:
            enhanced_context = stored_info
            logger.info(f"Using stored metadata for table {args.table_name}")
    
    # Generate prompt text using the dynamic configuration
    prompt_text = dynamic_loader.generate_prompt_text(
        prompt_config, 
        context=enhanced_context, 
        table_name=args.table_name
    )
    
    # Get suggestions (prompt-specific + global)
    suggestions = dynamic_loader.get_suggestions(prompt_config)
    
    # Add metadata-related suggestions for data_explainer
    if prompt_name == 'data_explainer':
        stored_tables = list_stored_tables()
        if stored_tables:
            suggestions.append(f"Stored metadata available for tables: {', '.join(stored_tables[:5])}{'...' if len(stored_tables) > 5 else ''}")
        suggestions.append("Provide field descriptions in format 'field_name: description' to store metadata")
    
    return PromptResult(prompt=prompt_text, suggestions=suggestions)

def get_available_dynamic_prompts() -> List[str]:
    """Get list of available dynamic prompts."""
    return dynamic_loader.list_prompts()

def reload_dynamic_prompts() -> bool:
    """Reload dynamic prompts from configuration file."""
    try:
        dynamic_loader.reload()
        logger.info("Dynamic prompts reloaded successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to reload dynamic prompts: {e}")
        return False

def has_dynamic_prompts() -> bool:
    """Check if any dynamic prompts are available."""
    return dynamic_loader.has_prompts()

def store_table_metadata_from_context(context: str, table_name: Optional[str] = None) -> bool:
    """Store table metadata from context for data_explainer prompt.
    
    This function parses field descriptions from context and stores them
    in the table metadata storage for future use.
    
    Args:
        context: Context string containing field descriptions
        table_name: Optional table name (will be extracted from context if not provided)
        
    Returns:
        bool: True if metadata was stored successfully
    """
    try:
        # Extract table name from context if not provided
        if not table_name:
            table_name = extract_table_name_from_context(context)
        
        if not table_name:
            logger.warning("No table name found in context for metadata storage")
            return False
        
        # Parse field descriptions from context
        field_descriptions = parse_field_descriptions(context)
        
        if not field_descriptions:
            logger.warning(f"No field descriptions found in context for table {table_name}")
            return False
        
        # Store metadata
        storage = get_table_metadata_storage()
        success = storage.bulk_update_from_descriptions(
            table_name=table_name,
            field_descriptions=field_descriptions
        )
        
        if success:
            logger.info(f"Stored metadata for table {table_name} with {len(field_descriptions)} fields")
        else:
            logger.error(f"Failed to store metadata for table {table_name}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error storing table metadata from context: {e}")
        return False

def get_stored_table_info(table_name: str, schema_name: Optional[str] = None) -> Optional[str]:
    """Retrieve stored table metadata as formatted context string.
    
    Args:
        table_name: Name of the table
        schema_name: Optional schema name
        
    Returns:
        Formatted context string or None if not found
    """
    try:
        storage = get_table_metadata_storage()
        metadata = storage.get_table_metadata(table_name, schema_name)
        
        if not metadata:
            return None
        
        # Format metadata as context string
        context_lines = [f"TABLE: {metadata.table_name}"]
        
        if metadata.description:
            context_lines.append(f"DESCRIPTION: {metadata.description}")
        
        # Add field descriptions
        for field in metadata.fields:
            if field.description:
                context_lines.append(f"{field.name}: {field.description}")
        
        return "\n".join(context_lines)
        
    except Exception as e:
        logger.error(f"Error retrieving stored table info for {table_name}: {e}")
        return None

def list_stored_tables() -> List[str]:
    """Get list of tables with stored metadata.
    
    Returns:
        List of table names with stored metadata
    """
    try:
        storage = get_table_metadata_storage()
        return storage.list_stored_tables()
    except Exception as e:
        logger.error(f"Error listing stored tables: {e}")
        return []