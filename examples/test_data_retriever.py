#!/usr/bin/env python3
"""
Test script to demonstrate the new data_retriever prompt functionality.
"""

import os
import sys
import tempfile
import json
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from db2_mcp_server.prompts.dynamic_loader import DynamicPromptLoader
from db2_mcp_server.prompts.db2_prompts import (
    dynamic_prompt,
    get_available_dynamic_prompts,
    has_dynamic_prompts
)

def test_data_retriever_prompt():
    """Test the new data_retriever prompt."""
    print("=== Testing Data Retriever Prompt ===")
    
    # Use the existing prompts_config.json
    config_path = Path(__file__).parent / "prompts_config.json"
    
    # Set environment variable
    os.environ["PROMPTS_FILE"] = str(config_path)
    
    try:
        # Test if dynamic prompts are available
        if has_dynamic_prompts():
            print("✓ Dynamic prompts are available")
            
            # Get available prompts
            available_prompts = get_available_dynamic_prompts()
            print(f"Available prompts: {available_prompts}")
            
            # Test the data_retriever prompt
            if "data_retriever" in available_prompts:
                print("\n✓ data_retriever prompt found")
                
                # Test with table name only
                result = dynamic_prompt(
                    prompt_name="data_retriever",
                    table_name="EMPLOYEES"
                )
                print("\n--- Data Retriever Prompt (Table Only) ---")
                print(f"Messages: {len(result.messages)}")
                for msg in result.messages:
                    print(f"Role: {msg.role}")
                    print(f"Content: {msg.content.text[:200]}...")
                
                # Test with context and table name
                result_with_context = dynamic_prompt(
                    prompt_name="data_retriever",
                    context="Need to find all employees hired in the last 6 months with salary > 50000",
                    table_name="EMPLOYEES"
                )
                print("\n--- Data Retriever Prompt (With Context) ---")
                print(f"Messages: {len(result_with_context.messages)}")
                for msg in result_with_context.messages:
                    print(f"Role: {msg.role}")
                    print(f"Content: {msg.content.text[:300]}...")
                    
            else:
                print("✗ data_retriever prompt not found in available prompts")
                
        else:
            print("✗ Dynamic prompts are not available")
            
    except Exception as e:
        print(f"✗ Error testing data_retriever prompt: {e}")
    
    finally:
        # Clean up environment variable
        if "PROMPTS_FILE" in os.environ:
            del os.environ["PROMPTS_FILE"]

def show_data_retriever_config():
    """Show the configuration for the data_retriever prompt."""
    print("\n=== Data Retriever Prompt Configuration ===")
    
    config_path = Path(__file__).parent / "prompts_config.json"
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Find the data_retriever prompt
        for prompt in config.get("prompts", []):
            if prompt.get("name") == "data_retriever":
                print(json.dumps(prompt, indent=2))
                break
        else:
            print("data_retriever prompt not found in configuration")
            
    except Exception as e:
        print(f"Error reading configuration: {e}")

if __name__ == "__main__":
    show_data_retriever_config()
    test_data_retriever_prompt()
    print("\n=== Test Complete ===")