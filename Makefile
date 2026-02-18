.PHONY: install test lint ingest preprocess rules embeddings weak-label train-baseline train-transformer infer evaluate active-learn pipeline clean

PYTHON ?= python
PYTEST ?= pytest
DATA_INPUT ?= data/raw/comments.jsonl
VENV ?= .venv

# -------------------------------------------------------------------
# Setup
# -------------------------------------------------------------------

install:
	pip install -r pipeline_requirements.txt

venv:
	python -m venv $(VENV)
	$(VENV)/bin/pip install -r pipeline_requirements.txt

# -------------------------------------------------------------------
# Testing
# -------------------------------------------------------------------

test:
	$(PYTEST) tests/ -v --tb=short

test-cov:
	$(PYTEST) tests/ -v --cov=src --cov-report=term-missing --tb=short

test-quick:
	$(PYTEST) tests/test_preprocess.py tests/test_rule_miner.py tests/test_schema.py -v --tb=short

# -------------------------------------------------------------------
# Pipeline stages
# -------------------------------------------------------------------

ingest:
	$(PYTHON) -c "from src.data_ingest import ingest, save_profile; \
		df = ingest('$(DATA_INPUT)'); \
		from src.utils.io_utils import project_root; \
		save_profile(df, project_root() / 'outputs')"

preprocess:
	$(PYTHON) -c "from src.data_ingest import ingest; \
		from src.preprocess import preprocess_dataframe; \
		df = ingest('$(DATA_INPUT)'); \
		df = preprocess_dataframe(df); \
		df.to_parquet('data/processed/preprocessed.parquet', index=False); \
		print(f'Preprocessed {len(df)} comments')"

rules:
	$(PYTHON) -c "import pandas as pd; \
		from src.rule_miner import RuleMiner; \
		df = pd.read_parquet('data/processed/preprocessed.parquet'); \
		miner = RuleMiner(); \
		df = miner.match_dataframe(df); \
		print(miner.coverage_report(df)); \
		df.to_parquet('data/processed/with_rules.parquet', index=False)"

embeddings:
	$(PYTHON) -c "import pandas as pd; \
		from src.embed_retrieval import EmbeddingRetriever; \
		df = pd.read_parquet('data/processed/with_rules.parquet'); \
		retriever = EmbeddingRetriever(); \
		df = retriever.match_dataframe(df); \
		df.to_parquet('data/processed/with_embeddings.parquet', index=False); \
		print(f'Added embeddings for {len(df)} comments')"

weak-label:
	$(PYTHON) -c "import pandas as pd; \
		from src.weak_label_llm import WeakLabeler; \
		df = pd.read_parquet('data/processed/with_embeddings.parquet'); \
		labeler = WeakLabeler(); \
		df = labeler.label_dataframe(df); \
		df.to_parquet('data/processed/weak_labeled.parquet', index=False); \
		print(f'Weak labeled {len(df)} comments')"

train-baseline:
	$(PYTHON) -c "import pandas as pd; \
		from src.train_baseline import train_tfidf_logreg; \
		df = pd.read_parquet('data/processed/weak_labeled.parquet'); \
		result = train_tfidf_logreg(df); \
		print(f'Baseline model saved to {result[\"model_dir\"]}')"

train-transformer:
	$(PYTHON) -c "import pandas as pd; \
		from src.train_transformer import train_transformer; \
		df = pd.read_parquet('data/processed/weak_labeled.parquet'); \
		result = train_transformer(df); \
		print(f'Transformer saved to {result[\"model_dir\"]}')"

infer:
	$(PYTHON) -m src.infer $(DATA_INPUT) -o outputs/predictions.jsonl \
		--baseline-model models/baseline_logreg

evaluate:
	$(PYTHON) -c "import json; \
		from src.evaluate import full_evaluation; \
		print('Run evaluation from notebook or after training.')"

active-learn:
	$(PYTHON) -c "import pandas as pd; \
		from src.active_learning import select_for_annotation, export_annotation_queue; \
		df = pd.read_parquet('data/processed/weak_labeled.parquet'); \
		selected = select_for_annotation(df); \
		path = export_annotation_queue(selected); \
		print(f'Exported {len(selected)} samples to {path}')"

# -------------------------------------------------------------------
# Full pipeline
# -------------------------------------------------------------------

pipeline: ingest preprocess rules embeddings weak-label train-baseline
	@echo "Pipeline complete."

# -------------------------------------------------------------------
# Cleanup
# -------------------------------------------------------------------

clean:
	rm -rf models/ outputs/ data/processed/
	rm -rf __pycache__ src/__pycache__ tests/__pycache__
	rm -rf .pytest_cache src/.pytest_cache
	find . -name "*.pyc" -delete
