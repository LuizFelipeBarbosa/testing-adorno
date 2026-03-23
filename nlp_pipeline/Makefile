.PHONY: install test test-cov test-quick pipeline clean

PYTHON ?= python
PYTEST ?= pytest

# -------------------------------------------------------------------
# Setup
# -------------------------------------------------------------------

install:
	pip install -r pipeline_requirements.txt

# -------------------------------------------------------------------
# Testing (run from repo root)
# -------------------------------------------------------------------

test:
	cd .. && $(PYTEST) nlp_pipeline/tests/ -v --tb=short

test-cov:
	cd .. && $(PYTEST) nlp_pipeline/tests/ -v --cov=nlp_pipeline --cov-report=term-missing --tb=short

test-quick:
	cd .. && $(PYTEST) nlp_pipeline/tests/test_preprocess.py nlp_pipeline/tests/test_rule_miner.py nlp_pipeline/tests/test_schema.py -v --tb=short

# -------------------------------------------------------------------
# Cleanup
# -------------------------------------------------------------------

clean:
	rm -rf __pycache__ tests/__pycache__
	rm -rf .pytest_cache
	find . -name "*.pyc" -delete
