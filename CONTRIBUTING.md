# Contributing to PyNipe

Thank you for your interest in contributing to PyNipe! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

Please be respectful and considerate of others when contributing to PyNipe. We aim to foster an inclusive and welcoming community.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up the development environment (see [INSTALL.md](INSTALL.md))
4. Create a new branch for your changes

## Development Workflow

1. Make your changes in your branch
2. Write or update tests for your changes
3. Run the tests to ensure they pass
4. Update documentation if necessary
5. Submit a pull request

## Pull Request Process

1. Ensure your code follows the project's style guidelines
2. Update the README.md or documentation with details of changes if appropriate
3. Make sure all CI checks pass
4. The pull request will be reviewed by maintainers
5. Address any feedback from the review
6. Once approved, your pull request will be merged

## Continuous Integration

We use GitHub Actions for continuous integration. The CI pipeline:

1. Runs tests on multiple Python versions
2. Checks code style with black and ruff
3. Builds the package to ensure it can be distributed

All pull requests must pass the CI checks before they can be merged.

## Coding Standards

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write docstrings for all functions, classes, and methods
- Keep functions and methods focused on a single responsibility
- Write tests for new functionality

## Pre-commit Hooks

We use pre-commit hooks to ensure code quality. To set up pre-commit:

1. Install development dependencies and pre-commit:
   ```bash
   uv pip install -e ".[dev]"
   ```

2. Install the git hooks:
   ```bash
   pre-commit install
   ```

3. The hooks will run automatically on each commit. They include:
   - black: Code formatting
   - isort: Import sorting
   - ruff: Linting
   - Various file checks (trailing whitespace, YAML validation, etc.)

You can also run the hooks manually on all files:
```bash
pre-commit run --all-files
```

Note: When pre-commit hooks modify files during a commit, the commit will be aborted. This is expected behavior. You need to stage the modified files and commit again:
```bash
git add .
git commit -m "Your commit message"
```

## Testing

- Write unit tests for all new functionality
- Ensure all tests pass before submitting a pull request
- Run tests with `pytest`
- Aim for high test coverage

## Documentation

- Update documentation for any changes to the API
- Write clear and concise docstrings
- Include examples where appropriate
- Keep the README.md up to date

## Reporting Bugs

When reporting bugs, please include:

- A clear and descriptive title
- Steps to reproduce the bug
- Expected behavior
- Actual behavior
- Any error messages or logs
- Your environment (Python version, OS, etc.)

## Feature Requests

When requesting features, please include:

- A clear and descriptive title
- A detailed description of the feature
- Why the feature would be useful
- Any potential implementation details

## Commit Messages

- Use clear and descriptive commit messages
- Start with a short summary line (50 chars or less)
- Optionally followed by a blank line and a more detailed explanation
- Reference issues and pull requests where appropriate

## Versioning

We use [Semantic Versioning](https://semver.org/) for versioning. For the versions available, see the tags on this repository.

## License

By contributing to PyNipe, you agree that your contributions will be licensed under the project's MIT license.
