#!/usr/bin/env python3
"""
Table Metadata CLI Utility

A command-line interface for managing table metadata storage.
This utility allows users to store, retrieve, and manage table metadata
for the data_explainer prompt.
"""

import sys
import os
import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from db2_mcp_server.storage import (
    get_table_metadata_storage,
    parse_field_descriptions,
    extract_table_name_from_context
)
from db2_mcp_server.prompts.db2_prompts import (
    store_table_metadata_from_context,
    get_stored_table_info,
    list_stored_tables
)

def store_from_file(file_path: str) -> bool:
    """Store table metadata from a file containing field descriptions.
    
    Expected file format:
    TABLE: table_name
    field1: description1
    field2: description2
    ...
    
    Args:
        file_path: Path to the file containing field descriptions
        
    Returns:
        bool: True if stored successfully
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        success = store_table_metadata_from_context(content)
        if success:
            table_name = extract_table_name_from_context(content)
            field_count = len(parse_field_descriptions(content))
            print(f"✓ Stored metadata for table '{table_name}' with {field_count} fields")
        else:
            print("✗ Failed to store metadata")
        
        return success
        
    except FileNotFoundError:
        print(f"✗ File not found: {file_path}")
        return False
    except Exception as e:
        print(f"✗ Error reading file: {e}")
        return False

def store_from_input(table_name: str, interactive: bool = False) -> bool:
    """Store table metadata from interactive input.
    
    Args:
        table_name: Name of the table
        interactive: Whether to use interactive mode
        
    Returns:
        bool: True if stored successfully
    """
    try:
        if interactive:
            print(f"Enter field descriptions for table '{table_name}'")
            print("Format: field_name: description")
            print("Press Enter twice to finish")
            print()
            
            lines = [f"TABLE: {table_name}"]
            while True:
                line = input("> ").strip()
                if not line:
                    break
                if ':' in line:
                    lines.append(line)
                else:
                    print("Invalid format. Use: field_name: description")
            
            context = "\n".join(lines)
        else:
            print(f"Enter field descriptions for table '{table_name}' (one per line):")
            print("Format: field_name: description")
            print("End with Ctrl+D (Unix) or Ctrl+Z (Windows)")
            print()
            
            lines = [f"TABLE: {table_name}"]
            try:
                for line in sys.stdin:
                    line = line.strip()
                    if line and ':' in line:
                        lines.append(line)
            except EOFError:
                pass
            
            context = "\n".join(lines)
        
        if len(lines) <= 1:
            print("✗ No field descriptions provided")
            return False
        
        success = store_table_metadata_from_context(context)
        if success:
            field_count = len(parse_field_descriptions(context))
            print(f"✓ Stored metadata for table '{table_name}' with {field_count} fields")
        else:
            print("✗ Failed to store metadata")
        
        return success
        
    except KeyboardInterrupt:
        print("\n✗ Operation cancelled")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def show_table_info(table_name: str, schema_name: Optional[str] = None) -> bool:
    """Display stored table metadata.
    
    Args:
        table_name: Name of the table
        schema_name: Optional schema name
        
    Returns:
        bool: True if table info was found and displayed
    """
    try:
        stored_info = get_stored_table_info(table_name, schema_name)
        if stored_info:
            print(f"Metadata for table '{table_name}':")
            print("-" * 40)
            print(stored_info)
            return True
        else:
            print(f"✗ No metadata found for table '{table_name}'")
            return False
            
    except Exception as e:
        print(f"✗ Error retrieving table info: {e}")
        return False

def list_tables() -> bool:
    """List all tables with stored metadata.
    
    Returns:
        bool: True if operation was successful
    """
    try:
        tables = list_stored_tables()
        if tables:
            print(f"Tables with stored metadata ({len(tables)}):")
            for i, table in enumerate(tables, 1):
                print(f"  {i}. {table}")
        else:
            print("No tables with stored metadata found")
        
        return True
        
    except Exception as e:
        print(f"✗ Error listing tables: {e}")
        return False

def delete_table_metadata(table_name: str, schema_name: Optional[str] = None) -> bool:
    """Delete stored table metadata.
    
    Args:
        table_name: Name of the table
        schema_name: Optional schema name
        
    Returns:
        bool: True if deleted successfully
    """
    try:
        storage = get_table_metadata_storage()
        success = storage.delete_table_metadata(table_name, schema_name)
        if success:
            print(f"✓ Deleted metadata for table '{table_name}'")
        else:
            print(f"✗ Failed to delete metadata for table '{table_name}'")
        
        return success
        
    except Exception as e:
        print(f"✗ Error deleting metadata: {e}")
        return False

def export_metadata(output_path: str, table_names: Optional[List[str]] = None) -> bool:
    """Export table metadata to a file.
    
    Args:
        output_path: Path to export file
        table_names: Optional list of table names to export
        
    Returns:
        bool: True if exported successfully
    """
    try:
        storage = get_table_metadata_storage()
        success = storage.export_metadata(output_path, table_names)
        if success:
            file_size = os.path.getsize(output_path)
            table_count = len(table_names) if table_names else len(list_stored_tables())
            print(f"✓ Exported metadata for {table_count} tables to '{output_path}' ({file_size} bytes)")
        else:
            print(f"✗ Failed to export metadata to '{output_path}'")
        
        return success
        
    except Exception as e:
        print(f"✗ Error exporting metadata: {e}")
        return False

def import_metadata(input_path: str) -> bool:
    """Import table metadata from a file.
    
    Args:
        input_path: Path to import file
        
    Returns:
        bool: True if imported successfully
    """
    try:
        storage = get_table_metadata_storage()
        success = storage.import_metadata(input_path)
        if success:
            print(f"✓ Imported metadata from '{input_path}'")
        else:
            print(f"✗ Failed to import metadata from '{input_path}'")
        
        return success
        
    except Exception as e:
        print(f"✗ Error importing metadata: {e}")
        return False

def create_sample_file(output_path: str) -> bool:
    """Create a sample field descriptions file.
    
    Args:
        output_path: Path to create sample file
        
    Returns:
        bool: True if created successfully
    """
    try:
        sample_content = """TABLE: sample_table
id: Unique identifier for the record
name: Human-readable name or title
description: Detailed description of the item
created_at: Timestamp when record was created
updated_at: Timestamp when record was last modified
status: Current status (active, inactive, pending)
user_id: Foreign key reference to users table
category: Classification or grouping of the item
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(sample_content)
        
        print(f"✓ Created sample file at '{output_path}'")
        print("Edit this file with your table and field descriptions, then use:")
        print(f"  python {sys.argv[0]} store --file {output_path}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error creating sample file: {e}")
        return False

def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Table Metadata CLI Utility for DB2 MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Store metadata from a file
  python table_metadata_cli.py store --file table_descriptions.txt
  
  # Store metadata interactively
  python table_metadata_cli.py store --table users --interactive
  
  # Show stored metadata for a table
  python table_metadata_cli.py show --table users
  
  # List all tables with metadata
  python table_metadata_cli.py list
  
  # Export metadata to a file
  python table_metadata_cli.py export --output metadata_backup.json
  
  # Import metadata from a file
  python table_metadata_cli.py import --input metadata_backup.json
  
  # Create a sample file template
  python table_metadata_cli.py sample --output sample_table.txt
"""
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Store command
    store_parser = subparsers.add_parser('store', help='Store table metadata')
    store_group = store_parser.add_mutually_exclusive_group(required=True)
    store_group.add_argument('--file', '-f', help='File containing field descriptions')
    store_group.add_argument('--table', '-t', help='Table name for interactive input')
    store_parser.add_argument('--interactive', '-i', action='store_true', 
                             help='Use interactive mode (with --table)')
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Show stored table metadata')
    show_parser.add_argument('--table', '-t', required=True, help='Table name')
    show_parser.add_argument('--schema', '-s', help='Schema name')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all tables with metadata')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete table metadata')
    delete_parser.add_argument('--table', '-t', required=True, help='Table name')
    delete_parser.add_argument('--schema', '-s', help='Schema name')
    delete_parser.add_argument('--confirm', action='store_true', help='Skip confirmation prompt')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export metadata to file')
    export_parser.add_argument('--output', '-o', required=True, help='Output file path')
    export_parser.add_argument('--tables', '-t', nargs='+', help='Specific tables to export')
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import metadata from file')
    import_parser.add_argument('--input', '-i', required=True, help='Input file path')
    
    # Sample command
    sample_parser = subparsers.add_parser('sample', help='Create sample field descriptions file')
    sample_parser.add_argument('--output', '-o', required=True, help='Output file path')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        if args.command == 'store':
            if args.file:
                success = store_from_file(args.file)
            else:
                success = store_from_input(args.table, args.interactive)
            return 0 if success else 1
            
        elif args.command == 'show':
            success = show_table_info(args.table, args.schema)
            return 0 if success else 1
            
        elif args.command == 'list':
            success = list_tables()
            return 0 if success else 1
            
        elif args.command == 'delete':
            if not args.confirm:
                response = input(f"Delete metadata for table '{args.table}'? (y/N): ")
                if response.lower() != 'y':
                    print("Operation cancelled")
                    return 0
            
            success = delete_table_metadata(args.table, args.schema)
            return 0 if success else 1
            
        elif args.command == 'export':
            success = export_metadata(args.output, args.tables)
            return 0 if success else 1
            
        elif args.command == 'import':
            success = import_metadata(args.input)
            return 0 if success else 1
            
        elif args.command == 'sample':
            success = create_sample_file(args.output)
            return 0 if success else 1
            
        else:
            parser.print_help()
            return 1
            
    except KeyboardInterrupt:
        print("\nOperation cancelled")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())