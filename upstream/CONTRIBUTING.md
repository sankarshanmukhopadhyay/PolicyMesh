# Contributing to PolicyMesh

Thank you for contributing.

![github-banner](https://github.com/Inky-Tech-Pty-Ltd/PolicyMesh/blob/main/images/PolicyMesh%20GitHub%20Banner.jpg)

### How to contribute:
1. Fork or create a feature branch from `main`:
   - git checkout -b feature/my-change
2. Create a virtual environment and install editable package:
   - python -m venv .venv
   - source .venv/bin/activate   # or .venv\Scripts\activate on Windows
   - pip install -e ".[dev]"     # if you add extra dev deps, otherwise pip install -e .
3. Run tests:
   - pytest
4. Commit and push, then open a Pull Request against `main`.
5. Follow PR template checklist (tests, lint, description).

### Maintainability:
- Keep functions small and add tests.
- Add type hints and docstrings where useful.
