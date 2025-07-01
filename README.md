# db2-mcp-server

[![PyPI version](https://badge.fury.io/py/db2-mcp-server.svg)](https://badge.fury.io/py/db2-mcp-server)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Coverage](https://img.shields.io/badge/coverage-90%25-brightgreen.svg)](https://github.com/huangjien/db2-mcp-server)

## Overview
The `db2-mcp-server` is a Python-based server utilizing the MCP framework to interact with IBM DB2 databases. It provides tools for listing tables and retrieving table metadata.

## Features
- **List Tables**: Retrieve a list of tables from the connected DB2 database.
- **Get Table Metadata**: Fetch metadata for a specific table, including column details and data types.
- **Dynamic Prompt Loading**: Load custom prompts from JSON configuration files for flexible query assistance.
- **Built-in Prompts**: Pre-configured prompts for DB2 query help and schema analysis.

## Requirements
- Python 3.12
- FastMCP (latest stable version)
- IBM DB2 Python driver (`ibm_db`)
- Pydantic

## Setup Instructions
1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd db2-mcp-server
   ```

2. **Set Up Virtual Environment**
   ```bash
   uv v0.6.x
   source uv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Server**
   ```bash
   python src/db2_mcp_server/core.py
   ```

## Dynamic Prompts
The server supports dynamic prompt loading from JSON configuration files. Set the `PROMPTS_FILE` environment variable to specify a custom prompts configuration file.

### Example Usage
```bash
export PROMPTS_FILE=/path/to/your/prompts_config.json
python src/db2_mcp_server/core.py
```

### Configuration Format
See `examples/prompts_config.json` for a complete example and `docs/DYNAMIC_PROMPTS.md` for detailed documentation.

## Testing
- Use `pytest` (version ≥ 7.0.0) for running tests.
- Current test coverage: **92.98%** (exceeding the 80% requirement).
- Comprehensive test suite includes:
  - Core functionality tests (`test_core.py`)
  - Database tools tests (`test_list_tables.py`, `test_metadata_retrieval.py`)
  - Caching mechanism tests (`test_cache.py`)
  - Logging configuration tests (`test_logger.py`)
  - Dynamic prompt loading tests (`test_dynamic_loader.py`, `test_integration_dynamic_prompts.py`)
- Run tests with:
  ```bash
  pytest --cov=src/db2_mcp_server --cov-report=html tests/
  ```
- For verbose output:
  ```bash
  pytest --cov=src/db2_mcp_server --cov-report=term-missing -v
  ```

## Security and API Restrictions
- The server is read-only, prohibiting SQL INSERT, UPDATE, or DELETE operations.
- Uses a database user with only SELECT privileges.

## Logging
- Errors are logged with structured logs in JSON format, excluding sensitive data.

## Contribution
- Contributions are welcome. Please follow the project's coding standards and testing guidelines.
