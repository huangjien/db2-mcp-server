#!/usr/bin/env python3
"""
Demonstration of the data_explainer prompt with user's example.
This script shows how to use field descriptions to generate SQL queries and explanations.
"""

import os
import sys
import json
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def demonstrate_data_explainer():
    """Demonstrate the data_explainer prompt configuration and usage."""
    print("=== Data Explainer Prompt Demonstration ===")
    print()
    
    # Show the prompt configuration
    config_path = Path(__file__).parent / "prompts_config.json"
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Find and display the data_explainer prompt
        for prompt in config.get("prompts", []):
            if prompt.get("name") == "data_explainer":
                print("📋 Data Explainer Prompt Configuration:")
                print(f"   Description: {prompt['description']}")
                print(f"   Category: {prompt['metadata']['category']}")
                print(f"   Operation Type: {prompt['metadata']['operation_type']}")
                print(f"   Complexity: {prompt['metadata']['complexity']}")
                print(f"   Features: {', '.join(prompt['metadata']['features'])}")
                print()
                
                print("🎯 Base Prompt:")
                print(f"   {prompt['base_prompt']}")
                print()
                
                print("💡 Key Suggestions:")
                for i, suggestion in enumerate(prompt['suggestions'], 1):
                    print(f"   {i}. {suggestion}")
                print()
                break
        
    except Exception as e:
        print(f"Error reading configuration: {e}")
        return
    
    # Show usage examples
    print("📝 Usage Examples:")
    print()
    
    examples = [
        {
            "title": "User Authentication Table (Your Example)",
            "description": "Simple user table with authentication fields",
            "table_name": "user",
            "field_descriptions": [
                "name: username",
                "password: digested password", 
                "last_login: timestamp of last login"
            ]
        },
        {
            "title": "Product Catalog Table",
            "description": "E-commerce product information",
            "table_name": "product",
            "field_descriptions": [
                "id: unique product identifier",
                "name: product name",
                "price: product price in USD",
                "category_id: foreign key to category table",
                "stock_quantity: available inventory count",
                "created_at: product creation timestamp",
                "is_active: boolean flag for product availability"
            ]
        },
        {
            "title": "Order Management Table",
            "description": "Customer order tracking",
            "table_name": "orders",
            "field_descriptions": [
                "order_id: unique order identifier",
                "customer_id: foreign key to customer table",
                "order_date: when the order was placed",
                "total_amount: total order value",
                "status: order status (pending, shipped, delivered, cancelled)",
                "shipping_address: delivery address",
                "payment_method: payment type used"
            ]
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"Example {i}: {example['title']}")
        print(f"Description: {example['description']}")
        print(f"Table: {example['table_name']}")
        print("Field Descriptions:")
        for field in example['field_descriptions']:
            print(f"  - {field}")
        print()
        
        # Show the context format
        context = f"TABLE: {example['table_name']}\n"
        context += "\n".join(example['field_descriptions'])
        
        print("Context Format for dynamic_prompt():")
        print('```')
        print(f'prompt_name="data_explainer",')
        print(f'context="""')
        print(context)
        print('""",')
        print(f'table_name="{example["table_name"]}"')
        print('```')
        print()
        
        print("Expected Output:")
        print("✓ SQL queries to retrieve and analyze data")
        print("✓ Detailed explanations of each field's purpose")
        print("✓ Suggestions for useful filtering and sorting")
        print("✓ Data type considerations and constraints")
        print("✓ Identification of relationships between fields")
        print("✓ Sample queries for common use cases")
        print()
        print("-" * 60)
        print()

def show_integration_example():
    """Show how to integrate the data_explainer prompt in a real application."""
    print("🔧 Integration Example:")
    print()
    
    integration_code = '''
# In your application code
from db2_mcp_server.prompts.db2_prompts import dynamic_prompt

def analyze_table_with_descriptions(table_name, field_descriptions):
    """Analyze a table using field descriptions."""
    
    # Format the context
    context = f"TABLE: {table_name}\\n"
    context += "\\n".join([f"{field}: {desc}" for field, desc in field_descriptions.items()])
    
    # Use the data_explainer prompt
    result = dynamic_prompt(
        prompt_name="data_explainer",
        context=context,
        table_name=table_name
    )
    
    return result

# Example usage
user_fields = {
    "name": "username",
    "password": "digested password",
    "last_login": "timestamp of last login"
}

result = analyze_table_with_descriptions("user", user_fields)
print(result.messages[0].content.text)
'''
    
    print(integration_code)
    print()

def main():
    """Main demonstration function."""
    demonstrate_data_explainer()
    show_integration_example()
    
    print("🎉 Data Explainer Prompt Demo Complete!")
    print()
    print("Next Steps:")
    print("1. Set the PROMPTS_FILE environment variable to use dynamic prompts")
    print("2. Call dynamic_prompt() with your table and field descriptions")
    print("3. Use the generated SQL queries and explanations in your application")
    print()
    print("For more information, see docs/DYNAMIC_PROMPTS.md")

if __name__ == "__main__":
    main()