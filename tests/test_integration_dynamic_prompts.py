import pytest
import json
import os
import tempfile
from unittest.mock import patch

from src.db2_mcp_server.prompts.db2_prompts import PromptInput, dynamic_prompt
from src.db2_mcp_server.prompts.dynamic_loader import dynamic_loader

class TestDynamicPromptIntegration:
    """Integration tests for dynamic prompt functionality."""
    
    def setup_method(self):
        """Set up test environment with sample configuration."""
        self.sample_config = {
            "version": "1.0",
            "global_suggestions": ["Use proper SQL syntax", "Consider performance"],
            "prompts": [
                {
                    "name": "test_analyzer",
                    "description": "Test analysis prompt",
                    "base_prompt": "Analyze the following database structure for testing purposes.",
                    "suggestions": ["Check test coverage", "Validate test data"],
                    "context_template": "Test context: {context}",
                    "table_template": "Focus on table '{table_name}' for testing.",
                    "metadata": {"category": "testing", "priority": "high"}
                },
                {
                    "name": "simple_helper",
                    "description": "Simple helper prompt",
                    "base_prompt": "Provide simple assistance with database queries."
                }
            ]
        }
    
    def test_dynamic_prompt_with_full_context(self):
        """Test dynamic prompt with context and table name."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.sample_config, f)
            temp_file = f.name
        
        try:
            with patch.dict(os.environ, {'PROMPTS_FILE': temp_file}):
                # Reload to pick up the new configuration
                dynamic_loader.reload()
                
                # Create prompt input
                prompt_input = PromptInput(
                    prompt_name="test_analyzer",
                    context="Performance testing scenario",
                    table_name="TEST_RESULTS"
                )
                
                # Call dynamic prompt function
                result = dynamic_prompt({}, prompt_input)
                
                # Verify the result
                assert result is not None
                expected_prompt = (
                    "Analyze the following database structure for testing purposes. "
                    "Focus on table 'TEST_RESULTS' for testing. "
                    "Test context: Performance testing scenario"
                )
                assert result.prompt == expected_prompt
                
                # Verify suggestions include both prompt-specific and global
                assert "Check test coverage" in result.suggestions
                assert "Validate test data" in result.suggestions
                assert "Use proper SQL syntax" in result.suggestions
                assert "Consider performance" in result.suggestions
                assert len(result.suggestions) == 4
        
        finally:
            os.unlink(temp_file)
    
    def test_dynamic_prompt_minimal_input(self):
        """Test dynamic prompt with minimal input."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.sample_config, f)
            temp_file = f.name
        
        try:
            with patch.dict(os.environ, {'PROMPTS_FILE': temp_file}):
                dynamic_loader.reload()
                
                # Create minimal prompt input
                prompt_input = PromptInput(prompt_name="simple_helper")
                
                # Call dynamic prompt function
                result = dynamic_prompt({}, prompt_input)
                
                # Verify the result
                assert result is not None
                assert result.prompt == "Provide simple assistance with database queries."
                
                # Should only have global suggestions
                assert "Use proper SQL syntax" in result.suggestions
                assert "Consider performance" in result.suggestions
                assert len(result.suggestions) == 2
        
        finally:
            os.unlink(temp_file)
    
    def test_dynamic_prompt_nonexistent_prompt(self):
        """Test dynamic prompt with nonexistent prompt name."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.sample_config, f)
            temp_file = f.name
        
        try:
            with patch.dict(os.environ, {'PROMPTS_FILE': temp_file}):
                dynamic_loader.reload()
                
                # Create prompt input with nonexistent prompt
                prompt_input = PromptInput(prompt_name="nonexistent_prompt")
                
                # Call dynamic prompt function
                result = dynamic_prompt({}, prompt_input)
                
                # Verify error handling
                assert result is not None
                assert "Dynamic prompt loading failed" in result.prompt
                assert "Available prompts: test_analyzer, simple_helper" in result.prompt
                assert "Check PROMPTS_FILE environment variable" in result.suggestions
        
        finally:
            os.unlink(temp_file)
    
    @patch.dict(os.environ, {}, clear=True)
    def test_dynamic_prompt_no_config_file(self):
        """Test dynamic prompt when no configuration file is set."""
        dynamic_loader.reload()
        
        # Create prompt input
        prompt_input = PromptInput(prompt_name="any_prompt")
        
        # Call dynamic prompt function
        result = dynamic_prompt({}, prompt_input)
        
        # Verify fallback behavior
        assert result is not None
        assert "Dynamic prompt loading failed" in result.prompt
        assert "No dynamic prompts loaded" in result.prompt
        assert "Check PROMPTS_FILE environment variable" in result.suggestions
    
    def test_dynamic_prompt_with_table_only(self):
        """Test dynamic prompt with only table name."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.sample_config, f)
            temp_file = f.name
        
        try:
            with patch.dict(os.environ, {'PROMPTS_FILE': temp_file}):
                dynamic_loader.reload()
                
                # Create prompt input with only table name
                prompt_input = PromptInput(
                    prompt_name="test_analyzer",
                    table_name="CUSTOMER_DATA"
                )
                
                # Call dynamic prompt function
                result = dynamic_prompt({}, prompt_input)
                
                # Verify the result
                assert result is not None
                expected_prompt = (
                    "Analyze the following database structure for testing purposes. "
                    "Focus on table 'CUSTOMER_DATA' for testing."
                )
                assert result.prompt == expected_prompt
        
        finally:
            os.unlink(temp_file)
    
    def test_dynamic_prompt_with_context_only(self):
        """Test dynamic prompt with only context."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.sample_config, f)
            temp_file = f.name
        
        try:
            with patch.dict(os.environ, {'PROMPTS_FILE': temp_file}):
                dynamic_loader.reload()
                
                # Create prompt input with only context
                prompt_input = PromptInput(
                    prompt_name="test_analyzer",
                    context="Security audit requirements"
                )
                
                # Call dynamic prompt function
                result = dynamic_prompt({}, prompt_input)
                
                # Verify the result
                assert result is not None
                expected_prompt = (
                    "Analyze the following database structure for testing purposes. "
                    "Test context: Security audit requirements"
                )
                assert result.prompt == expected_prompt
        
        finally:
            os.unlink(temp_file)