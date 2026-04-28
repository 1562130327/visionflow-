.PHONY: install run test lint clean

install:
	pip install -e .
	pip install -e ".[dev]"

run:
	uvicorn src.visionflow.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest tests/ -v

lint:
	ruff check src/
	mypy src/

clean:
	rm -rf __pycache__ .pytest_cache *.egg-info dist build
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
