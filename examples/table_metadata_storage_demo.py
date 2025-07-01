#!/usr/bin/env python3
"""
Table Metadata Storage Demo

This script demonstrates how to store and retrieve table metadata
for the data_explainer prompt using the new storage system.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from db2_mcp_server.storage import (
    TableMetadataStorage,
    TableMetadata,
    FieldInfo,
    get_table_metadata_storage,
    parse_field_descriptions,
    extract_table_name_from_context
)
from db2_mcp_server.prompts.db2_prompts import (
    store_table_metadata_from_context,
    get_stored_table_info,
    list_stored_tables
)

def demonstrate_basic_storage():
    """Demonstrate basic table metadata storage operations."""
    print("=== Basic Table Metadata Storage Demo ===")
    
    # Get storage instance
    storage = get_table_metadata_storage()
    
    # Create sample table metadata
    user_fields = [
        FieldInfo(
            name="user_id",
            data_type="INTEGER",
            description="Unique identifier for user",
            is_primary_key=True,
            business_context="Primary key for user authentication and identification"
        ),
        FieldInfo(
            name="username",
            data_type="VARCHAR(50)",
            description="User login name",
            is_nullable=False,
            business_context="Used for login authentication, must be unique"
        ),
        FieldInfo(
            name="email",
            data_type="VARCHAR(255)",
            description="User email address",
            is_nullable=False,
            business_context="Primary contact method, used for notifications"
        ),
        FieldInfo(
            name="password_hash",
            data_type="VARCHAR(255)",
            description="Hashed password for security",
            is_nullable=False,
            business_context="Encrypted password storage, never store plain text"
        ),
        FieldInfo(
            name="created_at",
            data_type="TIMESTAMP",
            description="Account creation timestamp",
            default_value="CURRENT_TIMESTAMP",
            business_context="Audit trail for account creation"
        ),
        FieldInfo(
            name="last_login",
            data_type="TIMESTAMP",
            description="Last successful login time",
            is_nullable=True,
            business_context="Track user activity and engagement"
        )
    ]
    
    user_metadata = TableMetadata(
        table_name="users",
        schema_name="auth",
        table_type="T",
        description="User authentication and profile information",
        fields=user_fields,
        business_purpose="Stores user account information for authentication and user management",
        sample_queries=[
            "SELECT * FROM auth.users WHERE username = ?",
            "SELECT user_id, username, last_login FROM auth.users WHERE last_login > ?",
            "SELECT COUNT(*) FROM auth.users WHERE created_at >= CURRENT_DATE - 30 DAYS"
        ]
    )
    
    # Store the metadata
    success = storage.store_table_metadata(user_metadata)
    print(f"Stored user table metadata: {success}")
    
    # Retrieve and display
    retrieved = storage.get_table_metadata("users", "auth")
    if retrieved:
        print(f"Retrieved metadata for: {retrieved.table_name}")
        print(f"Description: {retrieved.description}")
        print(f"Fields: {len(retrieved.fields)}")
        for field in retrieved.fields[:3]:  # Show first 3 fields
            print(f"  - {field.name}: {field.description}")
    
    print()

def demonstrate_context_parsing():
    """Demonstrate parsing field descriptions from context strings."""
    print("=== Context Parsing Demo ===")
    
    # Sample context with field descriptions
    context = """
TABLE: orders
order_id: Unique identifier for each order
user_id: Foreign key reference to users table
product_id: Foreign key reference to products table
quantity: Number of items ordered
order_date: Date when order was placed
status: Current order status (pending, shipped, delivered, cancelled)
total_amount: Total cost of the order including tax
shipping_address: Delivery address for the order
"""
    
    # Extract table name
    table_name = extract_table_name_from_context(context)
    print(f"Extracted table name: {table_name}")
    
    # Parse field descriptions
    field_descriptions = parse_field_descriptions(context)
    print(f"Parsed {len(field_descriptions)} field descriptions:")
    for field, desc in field_descriptions.items():
        print(f"  {field}: {desc}")
    
    # Store using context parsing
    success = store_table_metadata_from_context(context)
    print(f"Stored metadata from context: {success}")
    
    print()

def demonstrate_bulk_operations():
    """Demonstrate bulk metadata operations."""
    print("=== Bulk Operations Demo ===")
    
    storage = get_table_metadata_storage()
    
    # Bulk update from field descriptions
    product_descriptions = {
        "product_id": "Unique product identifier",
        "name": "Product name or title",
        "description": "Detailed product description",
        "price": "Product price in USD",
        "category_id": "Foreign key to product categories",
        "stock_quantity": "Available inventory count",
        "created_at": "Product creation timestamp",
        "updated_at": "Last modification timestamp"
    }
    
    success = storage.bulk_update_from_descriptions(
        table_name="products",
        field_descriptions=product_descriptions,
        table_description="Product catalog and inventory management"
    )
    print(f"Bulk update for products table: {success}")
    
    # List all stored tables
    stored_tables = list_stored_tables()
    print(f"Tables with stored metadata: {stored_tables}")
    
    print()

def demonstrate_data_explainer_integration():
    """Demonstrate integration with data_explainer prompt."""
    print("=== Data Explainer Integration Demo ===")
    
    # Sample context for data_explainer
    explainer_context = """
TABLE: customer_orders
customer_id: Unique customer identifier from CRM system
order_number: Human-readable order reference number
order_date: Date order was placed by customer
delivery_date: Expected or actual delivery date
order_value: Total monetary value of the order
payment_method: How customer paid (credit_card, paypal, bank_transfer)
order_status: Current fulfillment status
customer_notes: Special instructions from customer
"""
    
    # Store metadata using the data_explainer integration
    success = store_table_metadata_from_context(explainer_context)
    print(f"Stored data_explainer context: {success}")
    
    # Retrieve formatted context for reuse
    stored_info = get_stored_table_info("customer_orders")
    if stored_info:
        print("Retrieved stored context:")
        print(stored_info)
    
    print()

def demonstrate_export_import():
    """Demonstrate metadata export and import functionality."""
    print("=== Export/Import Demo ===")
    
    storage = get_table_metadata_storage()
    
    # Export metadata to file
    export_path = "/tmp/table_metadata_export.json"
    success = storage.export_metadata(export_path)
    print(f"Exported metadata to {export_path}: {success}")
    
    if success and os.path.exists(export_path):
        # Show file size
        file_size = os.path.getsize(export_path)
        print(f"Export file size: {file_size} bytes")
        
        # Clear some metadata and reimport
        storage.delete_table_metadata("users", "auth")
        print("Deleted users table metadata")
        
        # Import back
        import_success = storage.import_metadata(export_path)
        print(f"Imported metadata: {import_success}")
        
        # Verify import
        restored = storage.get_table_metadata("users", "auth")
        if restored:
            print(f"Restored users table with {len(restored.fields)} fields")
    
    print()

def demonstrate_advanced_features():
    """Demonstrate advanced metadata features."""
    print("=== Advanced Features Demo ===")
    
    storage = get_table_metadata_storage()
    
    # Update individual field description
    success = storage.update_field_description(
        table_name="orders",
        field_name="status",
        description="Order fulfillment status with workflow tracking",
        business_context="Critical for order processing pipeline and customer communication"
    )
    print(f"Updated field description: {success}")
    
    # Get updated metadata
    orders_metadata = storage.get_table_metadata("orders")
    if orders_metadata:
        status_field = next((f for f in orders_metadata.fields if f.name == "status"), None)
        if status_field:
            print(f"Updated status field: {status_field.description}")
            print(f"Business context: {status_field.business_context}")
    
    print()

def main():
    """Run all demonstrations."""
    print("Table Metadata Storage System Demo")
    print("=" * 50)
    print()
    
    try:
        demonstrate_basic_storage()
        demonstrate_context_parsing()
        demonstrate_bulk_operations()
        demonstrate_data_explainer_integration()
        demonstrate_export_import()
        demonstrate_advanced_features()
        
        print("=== Summary ===")
        stored_tables = list_stored_tables()
        print(f"Total tables with metadata: {len(stored_tables)}")
        print(f"Tables: {', '.join(stored_tables)}")
        
        print("\n=== Usage Instructions ===")
        print("1. Use store_table_metadata_from_context() to store field descriptions")
        print("2. Use get_stored_table_info() to retrieve formatted context")
        print("3. Use list_stored_tables() to see available metadata")
        print("4. The data_explainer prompt automatically stores and retrieves metadata")
        print("5. Export/import functionality allows backup and sharing of metadata")
        
    except Exception as e:
        print(f"Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()