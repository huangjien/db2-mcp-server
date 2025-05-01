# Project Development Rules: Read-Only DB2 MCP Server

This document outlines the rules and conventions for developing the Read-Only DB2 MCP Server.

## 1. Core Technologies

- **Programming Language:** Python 3.12
- **Package Management:** `uv` (Use `uv pip install`, `uv pip freeze > requirements.txt`, etc.)
- **Testing Framework:** `pytest`

## 2. Code Style and Conventions

- **Style Guide:** Follow PEP 8 guidelines for Python code.
- **Linting/Formatting:** Use tools like Ruff or Black (configured in the project) to ensure consistent code style. Run formatters/linters before committing.
- **Type Hinting:** Use Python type hints for all function signatures and complex variables to improve code clarity and enable static analysis.
- **Docstrings:** Write clear and concise docstrings for all modules, classes, functions, and methods following a standard format (e.g., Google Style, NumPy Style).
- **Logging:** Use the standard Python `logging` module for application logging. Configure appropriate log levels and handlers.

## 3. Version Control (Git)

- **Branching Strategy:** (Define your branching model, e.g., Gitflow, GitHub Flow). Typically, use feature branches for new development.
- **Commit Messages:** Write clear, concise, and informative commit messages. Follow conventional commit message formats if adopted.
- **Pull Requests:** All code changes must be submitted via Pull Requests (PRs). PRs require at least one review before merging.
- **Code Reviews:** Participate actively in code reviews, providing constructive feedback.

## 4. Dependency Management (`uv`)

- **Adding Dependencies:** Use `uv pip install <package>` to add new dependencies.
- **Updating `requirements.txt`:** After installing/updating dependencies, regenerate the `requirements.txt` (or `requirements-dev.txt`) file using `uv pip freeze > requirements.txt`.
- **Virtual Environments:** Always work within a virtual environment managed by `uv` (`uv venv`).

## 5. Testing (`pytest`)

- **Test Coverage:** Aim for high test coverage. All new features and bug fixes must include corresponding tests.
- **Test Location:** Keep tests in a dedicated `tests/` directory.
- **Test Naming:** Follow `pytest` conventions for test file (`test_*.py`) and test function (`test_*`) naming.
- **Running Tests:** Run tests frequently using the `pytest` command.
- **Mocking:** Use mocking libraries (e.g., `unittest.mock`, `pytest-mock`) to isolate units during testing, especially for database interactions.
- **Integration Tests:** Include integration tests that verify the interaction between different components, potentially using a test database instance.

## 6. Security

- **Credentials:** Never commit sensitive information (like database passwords or API keys) directly into the codebase. Use environment variables or a secure secrets management system.
- **Input Validation:** Rigorously validate and sanitize all external inputs (e.g., parameters in MCP tool requests) to prevent injection attacks (SQL injection, etc.).
- **Read-Only Principle:** Ensure all database interactions strictly adhere to the read-only principle.

## 7. Documentation

- **README.md:** Keep the main `README.md` updated with project setup, usage instructions, and basic architecture overview.
- **Design Document:** Maintain the `design.md` file, updating it as the architecture evolves.
- **Code Comments:** Use comments judiciously to explain complex logic or non-obvious code sections.