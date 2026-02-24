# Adorno Critique Detection Pipeline

Multi-label classifier that detects "non-standard critique" in YouTube comments, grounded in Adorno's Culture Industry theory.

## Labels

| Label                        | Description                                                  |
| ---------------------------- | ------------------------------------------------------------ |
| STANDARDIZATION              | Songs are formulaic / interchangeable / template-driven      |
| PSEUDO_INDIVIDUALIZATION     | Superficial uniqueness masking sameness                      |
| COMMODIFICATION_MARKET_LOGIC | Critique of charts / algorithms / labels / virality          |
| REGRESSIVE_LISTENING         | Passive / background / low-attention consumption             |
| AFFECTIVE_PREPACKAGING       | Emotion is engineered / prefabricated / manipulative         |
| FORMAL_RESISTANCE            | Recognition of complexity / anti-formula / genuine art       |
| NONE                         | No meaningful critique (auto-assigned when all others false) |

## Quick Start

```bash
# Install dependencies
pip install -r pipeline_requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY (optional, for LLM adjudication)

# Run tests
make test

# Prepare your data as CSV/JSON/JSONL with at least: comment_id, text
# Place it at ../data/raw/comments.jsonl

# Run full pipeline
make pipeline
```

## Pipeline Stages

```
Input (CSV/JSON/JSONL)
  │
  ├─ Stage 0: Data validation + profiling          (src/data_ingest.py)
  ├─ Stage 1: Text preprocessing + features         (src/preprocess.py)
  ├─ Stage 2: Rule-based high-precision detection    (src/rule_miner.py)
  ├─ Stage 3: Embedding semantic retrieval           (src/embed_retrieval.py)
  ├─ Stage 4: Weak supervision + LLM adjudication   (src/weak_label_llm.py)
  ├─ Stage 5: Supervised classifiers                 (src/train_baseline.py, src/train_transformer.py)
  ├─ Stage 6: Ensemble + calibrated thresholds       (src/infer.py)
  ├─ Stage 7: Evaluation                             (src/evaluate.py)
  └─ Stage 8: Active learning                        (src/active_learning.py)
  │
  Output (JSONL predictions)
```

## Running Individual Stages

```bash
make ingest          # Stage 0: validate + profile
make preprocess      # Stage 1: clean text + extract features
make rules           # Stage 2: apply regex rules
make embeddings      # Stage 3: compute embedding similarities
make weak-label      # Stage 4: combine signals + optional LLM
make train-baseline  # Stage 5a: TF-IDF + Logistic Regression
make train-transformer  # Stage 5b: fine-tune DistilBERT
make infer           # Stage 6: ensemble inference
make active-learn    # Stage 8: select samples for annotation
```

## Running Inference on New Data

```bash
python -m src.infer ../data/raw/new_comments.jsonl \
    -o outputs/predictions.jsonl \
    --baseline-model models/baseline_logreg
```

## Output Format

Each prediction in the JSONL output:

```json
{
  "comment_id": "abc123",
  "raw_text": "All these songs sound exactly the same",
  "predicted_labels": ["STANDARDIZATION"],
  "label_probs": {"STANDARDIZATION": 0.87, "PSEUDO_INDIVIDUALIZATION": 0.12, ...},
  "evidence": {"STANDARDIZATION": "rule match: 'songs sound the same'", ...},
  "decision_path": "ensemble",
  "needs_human_review": false
}
```

## Project Structure

```
configs/                  # YAML configuration files
  labels.yaml             # Label taxonomy and policies
  regex_rules.yaml        # Regex patterns per label
  model_config.yaml       # Model and pipeline parameters
  thresholds.yaml         # Per-label decision thresholds
docs/                     # Documentation
  taxonomy.md             # Precise label definitions
  annotation_guidelines.md # Human annotator instructions
  error_analysis.md       # Failure modes and mitigations
src/                      # Source modules
  data_ingest.py          # Stage 0: data loading + validation
  preprocess.py           # Stage 1: text cleaning + features
  rule_miner.py           # Stage 2: regex rule matching
  embed_retrieval.py      # Stage 3: embedding similarity
  weak_label_llm.py       # Stage 4: weak supervision + LLM
  train_baseline.py       # Stage 5a: TF-IDF classifiers
  train_transformer.py    # Stage 5b: transformer fine-tuning
  infer.py                # Stage 6: ensemble inference
  evaluate.py             # Stage 7: metrics + analysis
  active_learning.py      # Stage 8: uncertainty sampling
  prompts/                # LLM prompt templates
  utils/                  # Shared utilities
notebooks/                # Jupyter analysis notebooks
  01_eda.ipynb            # Exploratory data analysis
  02_rule_coverage.ipynb  # Rule matching analysis
  03_model_eval.ipynb     # Model evaluation + PR curves
tests/                    # Unit and schema tests
models/                   # Saved model artifacts (gitignored)
../data/                    # Input/processed data (gitignored)
outputs/                  # Predictions and reports (gitignored)
```

## Input Data Requirements

Minimum fields: `comment_id`, `text`

Optional: `video_id`, `like_count`, `published_at`, `language`

Missing fields are inferred safely (e.g., `comment_id` generated from text hash). Supported formats: CSV, JSON (array of objects), JSONL.

## Performance Targets

| Label                        | Target Precision | Target Recall |
| ---------------------------- | ---------------- | ------------- |
| STANDARDIZATION              | >= 0.80          | >= 0.60       |
| COMMODIFICATION_MARKET_LOGIC | >= 0.80          | >= 0.60       |
| FORMAL_RESISTANCE            | >= 0.65          | >= 0.60       |
| Others                       | >= 0.70          | >= 0.50       |

## Testing

```bash
make test         # all tests
make test-quick   # preprocessing + rules + schema only
make test-cov     # with coverage report
```
