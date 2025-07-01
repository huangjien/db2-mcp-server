#!/usr/bin/env python3
"""
Test script to demonstrate the new data_explainer prompt functionality.
This script shows how to use the prompt with field descriptions to explain table data.
"""

import os
import sys
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

def test_data_explainer_with_user_table():
    """Test the data_explainer prompt with the user's example table."""
    print("=== Testing Data Explainer Prompt with User Table ===")
    
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
            
            # Test the data_explainer prompt
            if "data_explainer" in available_prompts:
                print("\n✓ data_explainer prompt found")
                
                # User's example: TABLE: user with field descriptions
                user_table_context = """
TABLE: user
name: username
password: digested password
last_login: timestamp of last login

Please generate SQL queries to retrieve and analyze this user data, 
and explain what each field represents and how it can be used.
"""
                
                # Test with the user table example
                result = dynamic_prompt(
                    prompt_name="data_explainer",
                    context=user_table_context,
                    table_name="user"
                )
                
                print("\n--- Data Explainer Prompt for User Table ---")
                print(f"Messages: {len(result.messages)}")
                for i, msg in enumerate(result.messages, 1):
                    print(f"\nMessage {i}:")
                    print(f"Role: {msg.role}")
                    print(f"Content: {msg.content.text}")
                    print("-" * 50)
                
                # Test with another example - product table
                product_table_context = """
TABLE: product
id: unique product identifier
name: product name
price: product price in USD
category_id: foreign key to category table
stock_quantity: available inventory count
created_at: product creation timestamp
is_active: boolean flag for product availability

Generate queries to analyze product data and explain the business context.
"""
                
                result_product = dynamic_prompt(
                    prompt_name="data_explainer",
                    context=product_table_context,
                    table_name="product"
                )
                
                print("\n--- Data Explainer Prompt for Product Table ---")
                print(f"Messages: {len(result_product.messages)}")
                for i, msg in enumerate(result_product.messages, 1):
                    print(f"\nMessage {i}:")
                    print(f"Role: {msg.role}")
                    print(f"Content: {msg.content.text[:400]}...")  # Truncated for readability
                    print("-" * 50)
                    
            else:
                print("✗ data_explainer prompt not found in available prompts")
                
        else:
            print("✗ Dynamic prompts are not available")
            
    except Exception as e:
        print(f"✗ Error testing data_explainer prompt: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up environment variable
        if "PROMPTS_FILE" in os.environ:
            del os.environ["PROMPTS_FILE"]

def show_data_explainer_config():
    """Show the configuration for the data_explainer prompt."""
    print("\n=== Data Explainer Prompt Configuration ===")
    
    config_path = Path(__file__).parent / "prompts_config.json"
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Find the data_explainer prompt
        for prompt in config.get("prompts", []):
            if prompt.get("name") == "data_explainer":
                print(json.dumps(prompt, indent=2))
                break
        else:
            print("data_explainer prompt not found in configuration")
            
    except Exception as e:
        print(f"Error reading configuration: {e}")

def demonstrate_usage_examples():
    """Show usage examples for the data_explainer prompt."""
    print("\n=== Usage Examples ===")
    
    examples = [
        {
            "title": "User Authentication Table",
            "table": "user",
            "context": """
TABLE: user
name: username
password: digested password
last_login: timestamp of last login
"""
        },
        {
            "title": "E-commerce Product Table",
            "table": "product",
            "context": """
TABLE: product
id: unique product identifier
name: product name
price: product price in USD
category_id: foreign key to category table
stock_quantity: available inventory count
created_at: product creation timestamp
is_active: boolean flag for product availability
"""
        },
        {
            "title": "Order Management Table",
            "table": "orders",
            "context": """
TABLE: orders
order_id: unique order identifier
customer_id: foreign key to customer table
order_date: when the order was placed
total_amount: total order value
status: order status (pending, shipped, delivered, cancelled)
shipping_address: delivery address
payment_method: payment type used
"""
        }
    ]
    
    for example in examples:
        print(f"\n--- {example['title']} ---")
        print(f"Table: {example['table']}")
        print(f"Context: {example['context'].strip()}")
        print("\nThis would generate:")
        print("- SQL queries to retrieve and analyze the data")
        print("- Explanations of each field's purpose and meaning")
        print("- Suggestions for useful queries and data insights")
        print("- Data type considerations and constraints")

if __name__ == "__main__":
    show_data_explainer_config()
    demonstrate_usage_examples()
    test_data_explainer_with_user_table()
    print("\n=== Test Complete ===")