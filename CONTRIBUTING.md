# Contributing to Resource Grep

Thank you for your interest in contributing to Resource Grep! This document outlines the process for contributing to the project and provides guidelines to make the contribution process smooth for everyone.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contribution Workflow](#contribution-workflow)
- [Pull Request Guidelines](#pull-request-guidelines)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation Guidelines](#documentation-guidelines)
- [Issue Reporting Guidelines](#issue-reporting-guidelines)
- [Feature Request Guidelines](#feature-request-guidelines)
- [Communication Channels](#communication-channels)

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please read it before contributing.

## Getting Started

### Prerequisites

- Python 3.9+
- Docker and Docker Compose
- Git
- Basic knowledge of Elasticsearch, Redis, and FastAPI
- Familiarity with web crawling concepts (for crawler-related contributions)

### Understanding the Codebase

Before contributing, please take some time to understand the codebase structure:

- `api/`: FastAPI application for the REST API
- `streaming/`: FastAPI application for WebSocket streaming
- `crawler/`: Scrapy-based web crawler
- `static/`: Frontend static files
- `scripts/`: Utility scripts
- `elasticsearch/`: Elasticsearch mappings and configurations
- `docker/`: Docker-related files
- `tests/`: Test files

## Development Setup

1. **Fork the repository**:
   Click the "Fork" button at the top-right of the repository page.

2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/resource-grep.git
   cd resource-grep
   ```

3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/resource-grep/resource-grep.git
   ```

4. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

5. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   pip install -r crawler/requirements.txt
   ```

6. **Set up pre-commit hooks**:
   ```bash
   pre-commit install
   ```

7. **Start dependencies with Docker**:
   ```bash
   docker-compose up -d elasticsearch redis
   ```

8. **Initialize the database**:
   ```bash
   python scripts/init_db.py
   ```

9. **Start the development server**:
   ```bash
   uvicorn api.main:app --reload --port 8000
   ```

10. **Start the streaming server in another terminal**:
    ```bash
    uvicorn streaming.main:app --reload --port 8001
    ```

## Contribution Workflow

1. **Sync your fork with upstream**:
   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

2. **Create a new branch for your feature or bugfix**:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bugfix-name
   ```

3. **Make your changes and commit them**:
   ```bash
   git add .
   git commit -m "Description of your changes"
   ```

   Please follow these commit message guidelines:
   - Use the present tense ("Add feature" not "Added feature")
   - Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
   - Limit the first line to 72 characters or less
   - Reference issues and pull requests after the first line

4. **Push your changes**:
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request**:
   Go to your fork on GitHub and click the "New Pull Request" button.

## Pull Request Guidelines

- Each pull request should focus on a single feature or bugfix.
- Include tests for new features or bugfixes.
- Update documentation as needed.
- Make sure all tests pass before submitting the PR.
- Link the PR to any relevant issues.
- Add a clear description of the changes and why they are needed.
- Include screenshots or animated GIFs for UI changes if possible.

## Coding Standards

### Python

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide.
- Use type hints where appropriate.
- Document functions and classes using docstrings.
- Use meaningful variable names.
- Keep functions focused on a single responsibility.
- Maximum line length: 100 characters.

### JavaScript

- Follow the project's ESLint configuration.
- Use modern JavaScript features (ES6+).
- Avoid jQuery or other legacy libraries.
- Keep functions focused on a single responsibility.
- Use meaningful variable names.

### HTML/CSS

- Follow the project's existing style patterns.
- Use semantic HTML elements.
- Ensure accessibility guidelines are followed.
- Use CSS classes that follow a consistent naming convention.

## Testing Guidelines

### Test Coverage

- Aim for at least 80% test coverage for new code.
- Write unit tests for all new functions and classes.
- Write integration tests for API endpoints.
- Write end-to-end tests for critical user flows.

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_api.py

# Run tests with coverage report
pytest --cov=.
```

### Mocking

- Use mocks for external services (Elasticsearch, Redis).
- Use pytest fixtures for common test setups.
- Avoid network calls in unit tests.

## Documentation Guidelines

- Use Markdown for documentation.
- Keep documentation up-to-date with code changes.
- Document complex algorithms or business logic.
- Include examples where appropriate.
- Update the README.md file if necessary.
- Follow the existing documentation style.

## Issue Reporting Guidelines

When reporting issues, please use the provided issue templates and include:

1. **Clear and descriptive title**
2. **Steps to reproduce the issue**
3. **Expected behavior**
4. **Actual behavior**
5. **Screenshots or logs**, if applicable
6. **Environment information** (OS, browser, version, etc.)
7. **Possible solution** (if you have one)

## Feature Request Guidelines

When requesting features, please:

1. **Check existing issues** to make sure the feature hasn't been requested before.
2. **Describe the feature** in detail, including the problem it solves.
3. **Provide examples** of how the feature would be used.
4. **Explain why this feature would be valuable** to other users.
5. **Be open to discussion** about alternative approaches.

## Communication Channels

- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For general questions and discussions
- **Discord Server**: For real-time communication (link in README)
- **Dev Mailing List**: For development discussions (subscribe in README)

## Adding New Dependencies

Before adding a new dependency, consider the following:

1. Is the library actively maintained?
2. Is the library widely used and trusted?
3. What is the license of the library?
4. Could the functionality be implemented with existing dependencies?
5. What is the size and performance impact?

If you decide to add a new dependency, update the appropriate requirements file and document the reason for adding it in your PR.

## Working with Elasticsearch

When making changes to Elasticsearch mappings:

1. Create a new version of the mapping file.
2. Add a migration script in the `scripts/migrations/` directory.
3. Update the documentation to reflect the changes.
4. Make sure the API code is compatible with both old and new mappings.

## Working with the Crawler

When modifying the crawler:

1. Test crawling behavior locally first.
2. Be mindful of rate limiting and robots.txt compliance.
3. Document any changes to the crawler configuration.
4. Make sure extracted data maintains the expected schema.

## Licensing

By contributing to Resource Grep, you agree that your contributions will be licensed under the project's [MIT License](LICENSE). 