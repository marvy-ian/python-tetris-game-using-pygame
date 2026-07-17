# Contributing to Tetris

Thanks for your interest in contributing! This document outlines the process for contributing to this project.

## Getting Started

1. **Fork** the repository and clone your fork locally.
2. Create a new branch for your change:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Install dependencies:
   ```bash
   pip install pygame
   ```
4. Run the game locally to confirm everything works before making changes:
   ```bash
   python main.py
   ```

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue and include:

- A clear description of the problem
- Steps to reproduce it
- Expected vs. actual behavior
- Your OS, Python version, and Pygame version

### Suggesting Features

Feature suggestions are welcome. Please open an issue describing:

- The problem your feature would solve
- How you imagine it working
- Any relevant references (e.g. mechanics from other Tetris implementations)

### Submitting Changes

1. Keep pull requests focused — one feature or fix per PR is easiest to review.
2. Follow the existing code style (see below).
3. Test your changes manually by running the game and exercising the affected feature (movement, rotation, line clears, hold, pause, restart, game over, etc.).
4. Update the `README.md` if your change affects controls, features, or usage.
5. Write a clear commit message and PR description explaining **what** changed and **why**.

## Code Style

- Follow [PEP 8](https://peps.python.org/pep-0008/) conventions where reasonable.
- Keep functions small and focused — favor clarity over cleverness.
- Use descriptive names for variables and functions (e.g. `drop_interval`, `ghost_row`).
- Group related constants together (colors, shapes, layout) as done at the top of `main.py`.
- Avoid introducing new dependencies unless necessary; this project intentionally stays lightweight (Pygame only).

## Areas Open for Contribution

- Additional visual polish (animations, particle effects on line clear)
- Configurable key bindings
- High score persistence
- Alternate rotation systems (e.g. full SRS with proper kick tables)
- Gamepad support
- Unit tests for `Board` logic (line clearing, collision detection, scoring)

## Pull Request Checklist

Before submitting, please confirm:

- [ ] The game runs without errors (`python main.py`)
- [ ] Existing functionality still works as expected
- [ ] New functionality is documented in the README (if user-facing)
- [ ] Code follows the existing style and structure
- [ ] Commit messages are clear and descriptive

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## Questions?

If you're unsure about anything, feel free to open an issue to discuss before starting work on a larger change.