from pydantic import BaseModel, Field
from typing import List, Optional
from ..mcp_instance import mcp  # Import the shared mcp instance


class PromptInput(BaseModel):
  """Input schema for DB2 prompts."""

  context: Optional[str] = Field(None, description="Additional context for the prompt")
  table_name: Optional[str] = Field(None, description="Specific table to focus on")


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
    "Follow read-only access patterns",
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
    "Identify potential normalization issues",
  ]

  return PromptResult(prompt=prompt, suggestions=suggestions)
