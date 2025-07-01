import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

from src.db2_mcp_server.prompts.dynamic_loader import (
    DynamicPromptLoader,
    DynamicPromptConfig,
    DynamicPromptsConfig
)
from src.db2_mcp_server.prompts.db2_prompts import (
    get_available_dynamic_prompts,
    reload_dynamic_prompts,
    has_dynamic_prompts
)

class TestDynamicPromptConfig:
    """Test DynamicPromptConfig model."""
    
    def test_valid_config(self):
        """Test creating a valid prompt configuration."""
        config = DynamicPromptConfig(
            name="test_prompt",
            description="A test prompt",
            base_prompt="This is a test prompt",
            suggestions=["suggestion1", "suggestion2"],
            context_template="Context: {context}",
            table_template="Table: {table_name}",
            metadata={"category": "test"}
        )
        
        assert config.name == "test_prompt"
        assert config.description == "A test prompt"
        assert config.base_prompt == "This is a test prompt"
        assert len(config.suggestions) == 2
        assert config.context_template == "Context: {context}"
        assert config.table_template == "Table: {table_name}"
        assert config.metadata["category"] == "test"
    
    def test_minimal_config(self):
        """Test creating a minimal prompt configuration."""
        config = DynamicPromptConfig(
            name="minimal",
            description="Minimal prompt",
            base_prompt="Minimal"
        )
        
        assert config.name == "minimal"
        assert config.suggestions == []
        assert config.context_template is None
        assert config.table_template is None
        assert config.metadata == {}

class TestDynamicPromptsConfig:
    """Test DynamicPromptsConfig model."""
    
    def test_valid_config(self):
        """Test creating a valid prompts configuration."""
        prompt_config = DynamicPromptConfig(
            name="test",
            description="Test",
            base_prompt="Test prompt"
        )
        
        config = DynamicPromptsConfig(
            version="1.0",
            prompts=[prompt_config],
            global_suggestions=["global1", "global2"]
        )
        
        assert config.version == "1.0"
        assert len(config.prompts) == 1
        assert len(config.global_suggestions) == 2
    
    def test_default_values(self):
        """Test default values in configuration."""
        prompt_config = DynamicPromptConfig(
            name="test",
            description="Test",
            base_prompt="Test prompt"
        )
        
        config = DynamicPromptsConfig(prompts=[prompt_config])
        
        assert config.version == "1.0"
        assert config.global_suggestions == []

class TestDynamicPromptLoader:
    """Test DynamicPromptLoader class."""
    
    def setup_method(self):
        """Set up test environment."""
        self.sample_config = {
            "version": "1.0",
            "global_suggestions": ["global1", "global2"],
            "prompts": [
                {
                    "name": "test_prompt",
                    "description": "A test prompt",
                    "base_prompt": "This is a test prompt",
                    "suggestions": ["suggestion1", "suggestion2"],
                    "context_template": "Context: {context}",
                    "table_template": "Table: {table_name}",
                    "metadata": {"category": "test"}
                },
                {
                    "name": "simple_prompt",
                    "description": "A simple prompt",
                    "base_prompt": "Simple prompt text"
                }
            ]
        }
    
    @patch.dict(os.environ, {}, clear=True)
    def test_no_env_var(self):
        """Test loader when PROMPTS_FILE environment variable is not set."""
        loader = DynamicPromptLoader()
        
        assert loader.config is None
        assert len(loader.prompts_cache) == 0
        assert not loader.has_prompts()
    
    @patch.dict(os.environ, {'PROMPTS_FILE': '/nonexistent/file.json'})
    def test_nonexistent_file(self):
        """Test loader when prompts file doesn't exist."""
        loader = DynamicPromptLoader()
        
        assert loader.config is None
        assert len(loader.prompts_cache) == 0
        assert not loader.has_prompts()
    
    def test_valid_config_file(self):
        """Test loader with a valid configuration file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.sample_config, f)
            temp_file = f.name
        
        try:
            with patch.dict(os.environ, {'PROMPTS_FILE': temp_file}):
                loader = DynamicPromptLoader()
                
                assert loader.config is not None
                assert len(loader.prompts_cache) == 2
                assert loader.has_prompts()
                assert "test_prompt" in loader.prompts_cache
                assert "simple_prompt" in loader.prompts_cache
        finally:
            os.unlink(temp_file)
    
    def test_invalid_json(self):
        """Test loader with invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            temp_file = f.name
        
        try:
            with patch.dict(os.environ, {'PROMPTS_FILE': temp_file}):
                loader = DynamicPromptLoader()
                
                assert loader.config is None
                assert len(loader.prompts_cache) == 0
                assert not loader.has_prompts()
        finally:
            os.unlink(temp_file)
    
    def test_get_prompt(self):
        """Test getting a specific prompt configuration."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.sample_config, f)
            temp_file = f.name
        
        try:
            with patch.dict(os.environ, {'PROMPTS_FILE': temp_file}):
                loader = DynamicPromptLoader()
                
                prompt = loader.get_prompt("test_prompt")
                assert prompt is not None
                assert prompt.name == "test_prompt"
                assert prompt.description == "A test prompt"
                
                nonexistent = loader.get_prompt("nonexistent")
                assert nonexistent is None
        finally:
            os.unlink(temp_file)
    
    def test_list_prompts(self):
        """Test listing all available prompts."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.sample_config, f)
            temp_file = f.name
        
        try:
            with patch.dict(os.environ, {'PROMPTS_FILE': temp_file}):
                loader = DynamicPromptLoader()
                
                prompts = loader.list_prompts()
                assert len(prompts) == 2
                assert "test_prompt" in prompts
                assert "simple_prompt" in prompts
        finally:
            os.unlink(temp_file)
    
    def test_generate_prompt_text(self):
        """Test generating prompt text with templates."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.sample_config, f)
            temp_file = f.name
        
        try:
            with patch.dict(os.environ, {'PROMPTS_FILE': temp_file}):
                loader = DynamicPromptLoader()
                prompt_config = loader.get_prompt("test_prompt")
                
                # Test with both context and table
                text = loader.generate_prompt_text(
                    prompt_config, 
                    context="test context", 
                    table_name="test_table"
                )
                expected = "This is a test prompt Table: test_table Context: test context"
                assert text == expected
                
                # Test with only table
                text = loader.generate_prompt_text(
                    prompt_config, 
                    table_name="test_table"
                )
                expected = "This is a test prompt Table: test_table"
                assert text == expected
                
                # Test with only context
                text = loader.generate_prompt_text(
                    prompt_config, 
                    context="test context"
                )
                expected = "This is a test prompt Context: test context"
                assert text == expected
                
                # Test with neither
                text = loader.generate_prompt_text(prompt_config)
                expected = "This is a test prompt"
                assert text == expected
        finally:
            os.unlink(temp_file)
    
    def test_get_suggestions(self):
        """Test getting suggestions for a prompt."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.sample_config, f)
            temp_file = f.name
        
        try:
            with patch.dict(os.environ, {'PROMPTS_FILE': temp_file}):
                loader = DynamicPromptLoader()
                prompt_config = loader.get_prompt("test_prompt")
                
                suggestions = loader.get_suggestions(prompt_config)
                
                # Should include both prompt-specific and global suggestions
                assert "suggestion1" in suggestions
                assert "suggestion2" in suggestions
                assert "global1" in suggestions
                assert "global2" in suggestions
                assert len(suggestions) == 4
        finally:
            os.unlink(temp_file)
    
    def test_reload(self):
        """Test reloading prompts configuration."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.sample_config, f)
            temp_file = f.name
        
        try:
            with patch.dict(os.environ, {'PROMPTS_FILE': temp_file}):
                loader = DynamicPromptLoader()
                assert len(loader.prompts_cache) == 2
                
                # Modify the config and reload
                new_config = {
                    "version": "1.0",
                    "prompts": [
                        {
                            "name": "new_prompt",
                            "description": "New prompt",
                            "base_prompt": "New prompt text"
                        }
                    ]
                }
                
                with open(temp_file, 'w') as f:
                    json.dump(new_config, f)
                
                loader.reload()
                
                assert len(loader.prompts_cache) == 1
                assert "new_prompt" in loader.prompts_cache
                assert "test_prompt" not in loader.prompts_cache
        finally:
            os.unlink(temp_file)

class TestPromptFunctions:
    """Test the utility functions in db2_prompts module."""
    
    def setup_method(self):
        """Set up test environment."""
        self.sample_config = {
            "version": "1.0",
            "prompts": [
                {
                    "name": "test_prompt",
                    "description": "A test prompt",
                    "base_prompt": "This is a test prompt"
                }
            ]
        }
    
    def test_get_available_dynamic_prompts(self):
        """Test getting available dynamic prompts."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.sample_config, f)
            temp_file = f.name
        
        try:
            with patch.dict(os.environ, {'PROMPTS_FILE': temp_file}):
                # Force reload to pick up the new environment
                reload_dynamic_prompts()
                
                prompts = get_available_dynamic_prompts()
                assert "test_prompt" in prompts
        finally:
            os.unlink(temp_file)
    
    def test_has_dynamic_prompts(self):
        """Test checking if dynamic prompts are available."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.sample_config, f)
            temp_file = f.name
        
        try:
            with patch.dict(os.environ, {'PROMPTS_FILE': temp_file}):
                reload_dynamic_prompts()
                assert has_dynamic_prompts() is True
        finally:
            os.unlink(temp_file)
    
    @patch.dict(os.environ, {}, clear=True)
    def test_has_dynamic_prompts_false(self):
        """Test checking when no dynamic prompts are available."""
        reload_dynamic_prompts()
        assert has_dynamic_prompts() is False
    
    def test_reload_dynamic_prompts_success(self):
        """Test successful reload of dynamic prompts."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.sample_config, f)
            temp_file = f.name
        
        try:
            with patch.dict(os.environ, {'PROMPTS_FILE': temp_file}):
                result = reload_dynamic_prompts()
                assert result is True
        finally:
            os.unlink(temp_file)
    
    @patch.dict(os.environ, {}, clear=True)
    def test_reload_dynamic_prompts_no_file(self):
        """Test reload when no file is configured."""
        result = reload_dynamic_prompts()
        assert result is True  # Should succeed even with no file