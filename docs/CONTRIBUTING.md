# Contributing to flatexpy

Thank you for your interest in contributing to flatexpy! This document provides guidelines for contributing to the project.

## Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/ToAmano/flatexpy.git
   cd flatexpy
   ```

2. **Set up development environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e .[dev]
   ```

3. **Install pre-commit hooks**:
   ```bash
   pre-commit install
   ```

## Development Workflow

1. **Create a new branch** for your feature or bug fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the coding standards below.

3. **Run tests** to ensure everything works:
   ```bash
   pytest
   ```

4. **Run linting checks**:
   ```bash
   black flatexpy tests
   isort flatexpy tests
   flake8 flatexpy tests
   mypy flatexpy
   ```

5. **Commit your changes** with a descriptive message:
   ```bash
   git add .
   git commit -m "Add feature: description of your changes"
   ```

6. **Push your branch** and create a pull request:
   ```bash
   git push origin feature/your-feature-name
   ```

## Coding Standards

### Code Style
- Use [Black](https://black.readthedocs.io/) for code formatting (line length: 88)
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Follow [PEP 8](https://pep8.org/) style guidelines
- Use type hints for all function parameters and return values

### Documentation
- Write clear, concise docstrings for all public functions and classes
- Use Google-style docstrings
- Include examples in docstrings when helpful
- Update README.md for user-facing changes

### Testing
- Write unit tests for all new functionality
- Use pytest for testing
- Aim for high test coverage (>90%)
- Include integration tests for complex features
- Test edge cases and error conditions

### Git Commits
- Use clear, descriptive commit messages
- Start commit messages with a verb (Add, Fix, Update, etc.)
- Keep commit messages under 72 characters for the first line
- Include more details in the commit body if necessary

## Types of Contributions

### Bug Reports
When reporting bugs, please include:
- A clear description of the problem
- Steps to reproduce the issue
- Expected vs. actual behavior
- Your environment (OS, Python version, etc.)
- Minimal example that demonstrates the bug

### Feature Requests
When requesting features, please include:
- A clear description of the feature
- Why this feature would be useful
- Possible implementation approaches
- Examples of how the feature would be used

### Code Contributions
We welcome:
- Bug fixes
- New features
- Performance improvements
- Documentation improvements
- Test improvements

## Testing

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=flatexpy --cov-report=html

# Run specific test file
pytest tests/test_integration.py

# Run tests with verbose output
pytest -v
```

### Writing Tests
- Place unit tests in `tests/test_flatexpy.py`
- Place integration tests in `tests/test_integration.py`
- Use descriptive test names that explain what is being tested
- Test both success and failure cases
- Use fixtures for common test setup

## Release Process

Releases are handled by maintainers:

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Run release preparation script: `python scripts/prepare_release.py X.Y.Z`
4. Create git tag and GitHub release
5. Publish to PyPI via GitHub Actions

## Code Review Process

1. All changes must go through pull requests
2. At least one maintainer must approve the changes
3. All CI checks must pass
4. Code must maintain or improve test coverage
5. Documentation must be updated for user-facing changes

## Getting Help

- Create an issue for questions about contributing
- Check existing issues and pull requests first
- Be patient and respectful in all interactions

## Recognition

Contributors will be acknowledged in:
- GitHub contributors list
- Release notes for significant contributions
- README.md for major contributions

Thank you for contributing to flatexpy!
