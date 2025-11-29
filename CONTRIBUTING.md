# Contributing to GeoGuessr MCP Server

Thank you for your interest in contributing to the GeoGuessr MCP Server! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [License](#license)

## Code of Conduct

### Our Standards

- **Be Respectful**: Treat everyone with respect and professionalism
- **Be Collaborative**: Work together constructively
- **Be Patient**: Help others learn and grow
- **Be Inclusive**: Welcome diverse perspectives and backgrounds

### Unacceptable Behavior

- Harassment, discrimination, or offensive comments
- Personal attacks or trolling
- Publishing others' private information
- Any conduct that would be inappropriate in a professional setting

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/GeoGuessrMCP.git
   cd GeoGuessrMCP
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/NyxiumYuuki/GeoGuessrMCP.git
   ```

## Development Setup

### Prerequisites

- Python 3.13 or higher
- Docker and Docker Compose (for containerized development)
- Git

### Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Set up pre-commit hooks (optional but recommended)
pre-commit install
```

### Environment Configuration

Create a `.env` file with your configuration:

```env
GEOGUESSR_NCFA_COOKIE=your_cookie_here
MONITORING_ENABLED=true
MONITORING_INTERVAL_HOURS=24
LOG_LEVEL=DEBUG
```

## How to Contribute

### Reporting Bugs

Before creating a bug report:
1. **Check existing issues** to avoid duplicates
2. **Use the latest version** to verify the bug still exists
3. **Collect information**: version, OS, steps to reproduce

Create a detailed bug report including:
- Clear, descriptive title
- Steps to reproduce
- Expected vs. actual behavior
- Screenshots or logs (if applicable)
- Environment details

### Suggesting Enhancements

Enhancement suggestions are welcome! Include:
- Clear description of the proposed feature
- Rationale and use cases
- Examples of how it would work
- Any potential drawbacks or alternatives

### Contributing Code

1. **Find or create an issue** for the change you want to make
2. **Create a branch** from main:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-number-description
   ```
3. **Make your changes** following our coding standards
4. **Write tests** for your changes
5. **Run tests** to ensure nothing breaks
6. **Commit your changes** with clear messages
7. **Push to your fork** and create a pull request

## Coding Standards

### Python Style

We follow PEP 8 with some modifications:

- **Line length**: 100 characters (Black formatter)
- **Formatting**: Use Black for automatic formatting
- **Linting**: Use Ruff for code quality checks
- **Type hints**: Required for all functions (MyPy strict mode)

### Code Quality Tools

Run before committing:

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/

# Run all checks
black src/ tests/ && ruff check src/ tests/ && mypy src/
```

### Best Practices

1. **Keep functions focused**: One responsibility per function
2. **Use type hints**: All parameters and return values
3. **Write docstrings**: For all public functions and classes
4. **Avoid over-engineering**: Simple solutions are preferred
5. **Handle errors gracefully**: Use proper exception handling
6. **Log appropriately**: Use logging module, not print()

### Docstring Format

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """Brief description of function.

    Longer description if needed.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When something goes wrong
    """
    pass
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/geoguessr_mcp tests/

# Run specific test file
pytest tests/unit/test_specific.py

# Run tests matching a pattern
pytest -k "test_auth"

# Run with verbose output
pytest -v
```

### Writing Tests

- **Unit tests**: Test individual components in isolation
- **Integration tests**: Test component interactions
- **Mock external calls**: Use `respx` for HTTP mocking
- **Use fixtures**: Defined in `tests/conftest.py`
- **Test coverage**: Aim for 80%+ coverage on new code

Example test:

```python
import pytest
from geoguessr_mcp.services.profile import ProfileService

async def test_get_profile_success(mock_auth_session):
    """Test successful profile retrieval."""
    service = ProfileService(mock_auth_session)
    profile = await service.get_profile("user123")

    assert profile is not None
    assert profile.id == "user123"
```

## Pull Request Process

### Before Submitting

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New tests added for new features
- [ ] Documentation updated (if applicable)
- [ ] Commits are clear and atomic
- [ ] No merge conflicts with main branch

### PR Guidelines

1. **Title**: Clear, concise description
2. **Description**: Explain what and why, not how
3. **Link issues**: Reference related issues
4. **Screenshots**: Include for UI changes
5. **Breaking changes**: Clearly document

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Related Issues
Fixes #123

## Testing
Describe testing performed

## Checklist
- [ ] Tests pass
- [ ] Code follows style guide
- [ ] Documentation updated
```

### Review Process

1. **Automated checks**: CI/CD must pass
2. **Code review**: At least one approval required
3. **Owner approval**: Code owners must approve changes to owned files
4. **Feedback**: Address all review comments
5. **Merge**: Squash and merge (typically)

## Commit Message Guidelines

Follow conventional commits format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Formatting, no code change
- `refactor`: Code restructuring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples**:
```
feat(monitoring): add endpoint health checks

Implement periodic health checks for all monitored endpoints.
Includes retry logic and failure notifications.

Closes #42
```

```
fix(auth): handle expired cookie gracefully

Previously, expired cookies caused unhandled exceptions.
Now we catch and re-authenticate automatically.

Fixes #58
```

## Documentation

### When to Update Documentation

- Adding new features or tools
- Changing existing functionality
- Adding configuration options
- Updating dependencies or requirements

### Documentation Locations

- **README.md**: Overview, quick start, basic usage
- **CLAUDE.md**: Developer guide for AI assistants
- **Code comments**: Complex logic explanation
- **Docstrings**: All public APIs

## License

By contributing to GeoGuessr MCP Server, you agree that your contributions will be licensed under the MIT License.

## Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: Create an issue
- **Security**: Email yuki.vachot@datasingularity.fr

## Recognition

Contributors will be recognized in:
- GitHub contributors list
- Release notes (for significant contributions)
- Special mentions for major features

Thank you for contributing to GeoGuessr MCP Server! 🎉

---

**Maintainer**: Yûki VACHOT (@NyxiumYuuki)
**Last Updated**: 2025-11-29
