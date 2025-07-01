import os
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)

class DynamicPromptConfig(BaseModel):
    """Configuration for a dynamic prompt."""
    name: str = Field(..., description="Unique name for the prompt")
    description: str = Field(..., description="Description of what the prompt does")
    base_prompt: str = Field(..., description="Base prompt text")
    suggestions: List[str] = Field(default=[], description="List of suggestions")
    context_template: Optional[str] = Field(None, description="Template for context insertion")
    table_template: Optional[str] = Field(None, description="Template for table-specific prompts")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")

class DynamicPromptsConfig(BaseModel):
    """Configuration for all dynamic prompts."""
    version: str = Field("1.0", description="Configuration version")
    prompts: List[DynamicPromptConfig] = Field(..., description="List of prompt configurations")
    global_suggestions: List[str] = Field(default=[], description="Global suggestions for all prompts")

class DynamicPromptLoader:
    """Loader for dynamic prompts from JSON configuration."""
    
    def __init__(self):
        self.config: Optional[DynamicPromptsConfig] = None
        self.prompts_cache: Dict[str, DynamicPromptConfig] = {}
        self._load_prompts()
    
    def _load_prompts(self) -> None:
        """Load prompts from the JSON file specified in PROMPTS_FILE environment variable."""
        prompts_file = os.getenv('PROMPTS_FILE')
        
        if not prompts_file:
            logger.info("PROMPTS_FILE environment variable not set. Using default prompts only.")
            return
        
        prompts_path = Path(prompts_file)
        
        if not prompts_path.exists():
            logger.warning(f"Prompts file not found: {prompts_file}. Using default prompts only.")
            return
        
        try:
            with open(prompts_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.config = DynamicPromptsConfig(**data)
            
            # Cache prompts by name for quick lookup
            self.prompts_cache = {prompt.name: prompt for prompt in self.config.prompts}
            
            logger.info(f"Successfully loaded {len(self.config.prompts)} dynamic prompts from {prompts_file}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in prompts file {prompts_file}: {e}")
        except ValidationError as e:
            logger.error(f"Invalid prompts configuration in {prompts_file}: {e}")
        except Exception as e:
            logger.error(f"Error loading prompts from {prompts_file}: {e}")
    
    def get_prompt(self, name: str) -> Optional[DynamicPromptConfig]:
        """Get a prompt configuration by name."""
        return self.prompts_cache.get(name)
    
    def list_prompts(self) -> List[str]:
        """List all available dynamic prompt names."""
        return list(self.prompts_cache.keys())
    
    def has_prompts(self) -> bool:
        """Check if any dynamic prompts are loaded."""
        return bool(self.prompts_cache)
    
    def reload(self) -> None:
        """Reload prompts from the configuration file."""
        self.config = None
        self.prompts_cache.clear()
        self._load_prompts()
    
    def generate_prompt_text(self, prompt_config: DynamicPromptConfig, 
                           context: Optional[str] = None, 
                           table_name: Optional[str] = None) -> str:
        """Generate the final prompt text with context and table substitutions."""
        prompt_text = prompt_config.base_prompt
        
        # Apply table template if provided
        if table_name and prompt_config.table_template:
            table_text = prompt_config.table_template.format(table_name=table_name)
            prompt_text += f" {table_text}"
        elif table_name:
            prompt_text += f" Focus on the table: {table_name}"
        
        # Apply context template if provided
        if context and prompt_config.context_template:
            context_text = prompt_config.context_template.format(context=context)
            prompt_text += f" {context_text}"
        elif context:
            prompt_text += f" Additional context: {context}"
        
        return prompt_text
    
    def get_suggestions(self, prompt_config: DynamicPromptConfig) -> List[str]:
        """Get suggestions for a prompt, combining prompt-specific and global suggestions."""
        suggestions = prompt_config.suggestions.copy()
        
        if self.config and self.config.global_suggestions:
            suggestions.extend(self.config.global_suggestions)
        
        return suggestions

# Global instance
dynamic_loader = DynamicPromptLoader()