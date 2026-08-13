# Contributing to ArmPilot-AI

Thank you for your interest in contributing to ArmPilot-AI. This guide will help you get started.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/ArmPilot-AI.git`
3. Create a branch: `git checkout -b feature/your-feature`
4. Make your changes
5. Run tests: `bash scripts/test_all.sh`
6. Submit a pull request

## Development Setup

```bash
# Clone and setup
git clone https://github.com/your-username/ArmPilot-AI.git
cd ArmPilot-AI
bash scripts/setup.sh

# Start development server
bash scripts/run_server.sh
```

## Code Style

### Python

- Follow PEP 8
- Use type hints for all function signatures
- Keep functions under 30 lines where possible
- Use Pydantic models for all request/response schemas
- Docstrings for public functions (Google style)

### TypeScript/React

- Use double quotes for strings containing apostrophes
- Export components as default exports
- Use functional components with hooks
- Tailwind CSS for styling (no CSS modules)

### Commit Messages

Use conventional commits:

```
feat: add new optimization objective
fix: resolve TTFT measurement drift
docs: update API reference
test: add benchmark runner tests
refactor: extract hardware detection utils
```

## Project Structure

```
backend/
├── app/api/         # Route handlers (thin)
├── app/services/    # Business logic
├── app/schemas/     # Pydantic models
├── app/benchmark/   # Benchmark engine
├── app/optimization/# Optimization engine
└── app/core/        # Infrastructure

src/                  # React frontend
configs/              # YAML configuration
scripts/              # Shell utilities
```

## Adding Features

### New API Endpoint

1. Add schema in `backend/app/schemas/`
2. Add service method in `backend/app/services/`
3. Add route handler in `backend/app/api/`
4. Register route in `backend/app/api/router.py`
5. Add tests in `backend/tests/`

### New Benchmark Metric

1. Add collector in `backend/app/benchmark/`
2. Add to `BenchmarkResult` schema
3. Update report builder
4. Add to recommendation engine rules

### New Optimization Parameter

1. Add to search space in `configs/optimization.yaml`
2. Add optimizer in `backend/app/optimization/`
3. Add hardware profile recommendations
4. Update scoring algorithm

## Testing

```bash
# Run all tests
bash scripts/test_all.sh

# Run specific test file
cd backend
python3 -m pytest tests/test_benchmark.py -v

# Run with coverage
python3 -m pytest tests/ --cov=app --cov-report=html
```

## Pull Request Process

1. Ensure all tests pass
2. Update documentation if needed
3. Add changelog entry
4. Request review from maintainers
5. Address review feedback
6. Squash and merge

## Reporting Issues

Use GitHub Issues with the appropriate template:

- **Bug Report** — Steps to reproduce, expected vs actual behavior
- **Feature Request** — Problem description, proposed solution
- **Performance** — Hardware specs, model, configuration, metrics

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
