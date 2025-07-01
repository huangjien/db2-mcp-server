#!/usr/bin/env python3
"""
Example script demonstrating the dynamic prompt loading feature.

This script shows how to:
1. Set up a dynamic prompts configuration
2. Load prompts from a JSON file
3. Use the dynamic prompts through the MCP interface
4. Handle different scenarios (success, errors, fallbacks)

Usage:
    python examples/dynamic_prompts_example.py
"""

import os
import json
import tempfile
from pathlib import Path

# Add the src directory to the path so we can import our modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from db2_mcp_server.prompts.db2_prompts import (
    PromptInput, 
    dynamic_prompt,
    get_available_dynamic_prompts,
    reload_dynamic_prompts,
    has_dynamic_prompts
)
from db2_mcp_server.prompts.dynamic_loader import dynamic_loader

def create_sample_config():
    """Create a sample configuration for demonstration."""
    return {
        "version": "1.0",
        "global_suggestions": [
            "Always backup before making changes",
            "Test queries in development first",
            "Monitor performance impact"
        ],
        "prompts": [
            {
                "name": "performance_optimizer",
                "description": "Optimize DB2 database performance",
                "base_prompt": "You are a DB2 performance expert. Analyze the database structure and provide specific optimization recommendations.",
                "suggestions": [
                    "Check index usage statistics",
                    "Analyze query execution plans",
                    "Review buffer pool configurations",
                    "Consider table partitioning"
                ],
                "context_template": "Performance analysis context: {context}",
                "table_template": "Focus optimization efforts on table '{table_name}' and its related indexes.",
                "metadata": {
                    "category": "performance",
                    "expertise_level": "advanced",
                    "estimated_time": "30-60 minutes"
                }
            },
            {
                "name": "quick_helper",
                "description": "Quick assistance with common DB2 tasks",
                "base_prompt": "Provide quick, practical help with DB2 database tasks.",
                "suggestions": [
                    "Check syntax documentation",
                    "Use EXPLAIN for query analysis"
                ],
                "metadata": {
                    "category": "general",
                    "expertise_level": "beginner"
                }
            },
            {
                "name": "security_checker",
                "description": "Security analysis and recommendations",
                "base_prompt": "Perform a comprehensive security analysis of the DB2 database configuration and access patterns.",
                "suggestions": [
                    "Review user privileges and roles",
                    "Check for unused accounts",
                    "Validate encryption settings",
                    "Audit access logs"
                ],
                "context_template": "Security audit scope: {context}",
                "table_template": "Perform security analysis on table '{table_name}' including column-level permissions.",
                "metadata": {
                    "category": "security",
                    "compliance": ["SOX", "GDPR"],
                    "risk_level": "high"
                }
            }
        ]
    }

def demonstrate_dynamic_prompts():
    """Demonstrate the dynamic prompt loading feature."""
    print("=" * 60)
    print("DB2 MCP Server - Dynamic Prompts Demonstration")
    print("=" * 60)
    
    # Create a temporary configuration file
    config = create_sample_config()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config, f, indent=2)
        config_file = f.name
    
    try:
        # Set the environment variable
        os.environ['PROMPTS_FILE'] = config_file
        print(f"\n1. Configuration file created: {config_file}")
        
        # Reload prompts to pick up the new configuration
        reload_success = reload_dynamic_prompts()
        print(f"2. Prompts loaded successfully: {reload_success}")
        
        # Check if prompts are available
        has_prompts = has_dynamic_prompts()
        print(f"3. Dynamic prompts available: {has_prompts}")
        
        # List available prompts
        available_prompts = get_available_dynamic_prompts()
        print(f"4. Available prompts: {', '.join(available_prompts)}")
        
        print("\n" + "="*60)
        print("DEMONSTRATION SCENARIOS")
        print("="*60)
        
        # Scenario 1: Performance optimization with full context
        print("\nScenario 1: Performance Optimization (Full Context)")
        print("-" * 50)
        
        prompt_input = PromptInput(
            prompt_name="performance_optimizer",
            context="Database response time has increased by 40% over the past month",
            table_name="CUSTOMER_ORDERS"
        )
        
        result = dynamic_prompt({}, prompt_input)
        print(f"Prompt: {result.prompt}")
        print(f"Suggestions ({len(result.suggestions)}):")
        for i, suggestion in enumerate(result.suggestions, 1):
            print(f"  {i}. {suggestion}")
        
        # Scenario 2: Quick help with minimal input
        print("\nScenario 2: Quick Help (Minimal Input)")
        print("-" * 50)
        
        prompt_input = PromptInput(prompt_name="quick_helper")
        result = dynamic_prompt({}, prompt_input)
        print(f"Prompt: {result.prompt}")
        print(f"Suggestions ({len(result.suggestions)}):")
        for i, suggestion in enumerate(result.suggestions, 1):
            print(f"  {i}. {suggestion}")
        
        # Scenario 3: Security analysis with table focus
        print("\nScenario 3: Security Analysis (Table Focus)")
        print("-" * 50)
        
        prompt_input = PromptInput(
            prompt_name="security_checker",
            table_name="EMPLOYEE_RECORDS",
            context="Preparing for SOX compliance audit"
        )
        
        result = dynamic_prompt({}, prompt_input)
        print(f"Prompt: {result.prompt}")
        print(f"Suggestions ({len(result.suggestions)}):")
        for i, suggestion in enumerate(result.suggestions, 1):
            print(f"  {i}. {suggestion}")
        
        # Scenario 4: Error handling - nonexistent prompt
        print("\nScenario 4: Error Handling (Nonexistent Prompt)")
        print("-" * 50)
        
        prompt_input = PromptInput(prompt_name="nonexistent_prompt")
        result = dynamic_prompt({}, prompt_input)
        print(f"Error Response: {result.prompt}")
        print(f"Error Suggestions: {result.suggestions}")
        
        # Scenario 5: No configuration file
        print("\nScenario 5: No Configuration File")
        print("-" * 50)
        
        # Temporarily remove the environment variable
        del os.environ['PROMPTS_FILE']
        reload_dynamic_prompts()
        
        prompt_input = PromptInput(prompt_name="any_prompt")
        result = dynamic_prompt({}, prompt_input)
        print(f"Fallback Response: {result.prompt}")
        print(f"Fallback Suggestions: {result.suggestions}")
        
        print("\n" + "="*60)
        print("DEMONSTRATION COMPLETE")
        print("="*60)
        print("\nKey Features Demonstrated:")
        print("✓ Loading prompts from JSON configuration")
        print("✓ Template substitution for context and table names")
        print("✓ Combining prompt-specific and global suggestions")
        print("✓ Error handling for missing prompts")
        print("✓ Graceful fallback when no configuration is available")
        print("✓ Runtime reloading of configurations")
        
        print("\nNext Steps:")
        print("1. Create your own prompts_config.json file")
        print("2. Set PROMPTS_FILE environment variable")
        print("3. Use dynamic_prompt in your MCP applications")
        print("4. Customize prompts for your specific use cases")
        
    finally:
        # Clean up
        if os.path.exists(config_file):
            os.unlink(config_file)
        # Restore environment if needed
        if 'PROMPTS_FILE' in os.environ:
            del os.environ['PROMPTS_FILE']

def show_configuration_example():
    """Show an example of the JSON configuration format."""
    print("\n" + "="*60)
    print("EXAMPLE CONFIGURATION FILE")
    print("="*60)
    
    config = create_sample_config()
    print(json.dumps(config, indent=2))
    
    print("\nConfiguration Explanation:")
    print("- 'version': Configuration format version")
    print("- 'global_suggestions': Apply to all prompts")
    print("- 'prompts': Array of prompt configurations")
    print("  - 'name': Unique identifier for the prompt")
    print("  - 'description': Human-readable description")
    print("  - 'base_prompt': Main prompt text")
    print("  - 'suggestions': Prompt-specific suggestions")
    print("  - 'context_template': Template for context insertion")
    print("  - 'table_template': Template for table name insertion")
    print("  - 'metadata': Additional information (optional)")

if __name__ == "__main__":
    try:
        demonstrate_dynamic_prompts()
        show_configuration_example()
    except Exception as e:
        print(f"Error during demonstration: {e}")
        import traceback
        traceback.print_exc()