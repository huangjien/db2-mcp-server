from src.db2_mcp_server.prompts.db2_prompts import db2_query_helper, PromptInput


def test_db2_query_helper():
  args = PromptInput(table_name="TEST_TABLE", context="Sample context")
  result = db2_query_helper(None, args)
  assert "TEST_TABLE" in result.prompt
  assert len(result.suggestions) > 0
