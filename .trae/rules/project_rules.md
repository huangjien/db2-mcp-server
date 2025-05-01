1. Framework & Dependencies
Python & MCP Framework

Python: Exactly 3.12.

FastMCP: alway try latest stable version in pyproject.toml. 
Axolo

uv: Use uv v0.6.x for virtual-environment and dependency management.

Dependency Locking

List all dependencies (e.g. fastmcp, ibm_db client, pydantic) in pyproject.toml.

Maintain a uv.lock to ensure reproducible builds. 
Software Engineering Stack Exchange

2. Testing Framework
pytest

Require pytest ≥ 7.0.0.

Fixtures:

Use yield-style fixtures for setup/teardown. 
Stack Overflow

Keep fixtures modular and place shared ones in conftest.py. 
Python Tutorials – Real Python

For global setup/teardown, use fixtures with scope="session". 
Stack Overflow

Isolation & Coverage:

Tests must be independent and mock external I/O. 
Medium

Aim for ≥ 90% code coverage.

Continuous Integration:

Run pytest with --strict-markers, --cov, and fail on any warnings.

3. API & Security Restrictions
Read-Only Enforcement

Prohibit any SQL INSERT, UPDATE, or DELETE—both via user credentials and code patterns.

Use a database user with only SELECT privileges.

Forbidden APIs

Do not use eval(), exec(), or any dynamic code-execution functions. 
blog.codacy.com

Avoid usage of internal or private database APIs—stick to the official IBM Db2 Python driver (ibm_db).

Error Handling & Logging

Log errors with structured logs (JSON) without sensitive data.

Fail fast on schema mismatches or unexpected result shapes.

