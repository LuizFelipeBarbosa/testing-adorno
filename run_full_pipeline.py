"""Full pipeline: Stages 0-8 on YouTube comments data.

Runs:
  Stage 0: Data ingestion + validation
  Stage 1: Text preprocessing + features
  Stage 2: Rule-based detection
  Stage 3: Embedding retrieval
  Stage 4: Weak supervision (no LLM - no API key)
  Stage 5a: TF-IDF + LogReg baseline training
  Stage 5b: (Skipped - DistilBERT takes too long without GPU)
  Stage 6: Ensemble inference
  Stage 7: Evaluation
  Stage 8: Active learning sample selection
"""

import sys
import time
import json
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", category=FutureWarning)

sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
import pandas as pd

from src.data_ingest import ingest, save_profile
from src.preprocess import preprocess_dataframe
from src.rule_miner import RuleMiner
from src.embed_retrieval import EmbeddingRetriever
from src.weak_label_llm import WeakLabeler, CRITIQUE_LABELS
from src.train_baseline import train_tfidf_logreg
from src.evaluate import compute_metrics, full_evaluation
from src.active_learning import select_for_annotation, export_annotation_queue
from src.utils.io_utils import ensure_dir, save_json, save_jsonl
from src.utils.seed import set_global_seed

set_global_seed(42)

DATA_PATH = Path("data/raw/comments.json")
OUTPUT_DIR = Path("outputs")
MODELS_DIR = Path("models")
ensure_dir(OUTPUT_DIR)
ensure_dir(MODELS_DIR)

t_start = time.time()


# ═══════════════════════════════════════════════════════════════════════════
# STAGE 0: Data Ingestion
# ═══════════════════════════════════════════════════════════════════════════
print("=" * 70)
print("  STAGE 0: Data Ingestion + Validation")
print("=" * 70)
t0 = time.time()
df = ingest(DATA_PATH)
profile = df.attrs.get("profile", {})
save_profile(profile, OUTPUT_DIR / "eval")
print(f"  Rows: {len(df)}")
print(f"  Emoji-only: {profile.get('emoji_only_count', '?')}")
print(f"  Text length mean: {profile.get('text_length', {}).get('mean', '?')}")
print(f"  Time: {time.time() - t0:.1f}s")


# ═══════════════════════════════════════════════════════════════════════════
# STAGE 1: Preprocessing
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("  STAGE 1: Text Preprocessing + Feature Extraction")
print("=" * 70)
t1 = time.time()
df = preprocess_dataframe(df)
trivial_n = df["is_trivial"].sum()
trivial_pct = df["is_trivial"].mean() * 100
lang_top = df["language"].value_counts().head(5)
print(f"  Trivial comments: {trivial_n} ({trivial_pct:.1f}%)")
print(f"  Top languages: {dict(lang_top)}")
print(f"  Time: {time.time() - t1:.1f}s")


# ═══════════════════════════════════════════════════════════════════════════
# STAGE 2: Rule Mining
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("  STAGE 2: Rule-Based Critique Detection")
print("=" * 70)
t2 = time.time()
miner = RuleMiner()
df = miner.match_dataframe(df)
report = miner.coverage_report(df)
print(f"  Any rule match: {report['any_rule_hit']} ({report['any_rule_hit_pct']:.1f}%)")
for label, stats in report["per_label"].items():
    print(f"    {label:40s}  {stats['hits']:6d}  ({stats['hit_pct']:.2f}%)")
save_json(report, OUTPUT_DIR / "rule_coverage_report.json")
print(f"  Time: {time.time() - t2:.1f}s")


# ═══════════════════════════════════════════════════════════════════════════
# STAGE 3: Embedding Retrieval
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("  STAGE 3: Embedding Retrieval (sentence-transformers)")
print("=" * 70)
t3 = time.time()
retriever = EmbeddingRetriever()
df = retriever.match_dataframe(df, text_col="clean_text", batch_size=512)

# Report top scores per label
print("  Embedding similarity summary:")
for lbl in CRITIQUE_LABELS:
    col = f"emb_{lbl}_score"
    if col in df.columns:
        scores = df[col]
        above_thresh = (scores >= 0.45).sum()
        print(f"    {lbl:40s}  above 0.45: {above_thresh:6d}  max: {scores.max():.3f}  mean: {scores.mean():.3f}")
print(f"  Time: {time.time() - t3:.1f}s")


# ═══════════════════════════════════════════════════════════════════════════
# STAGE 4: Weak Supervision (rule + embedding combination, no LLM)
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("  STAGE 4: Weak Supervision (combining rule + embedding signals)")
print("=" * 70)
t4 = time.time()
labeler = WeakLabeler()
df = labeler.label_dataframe(df, use_llm=False)

# Report weak label distribution
print("  Weak label distribution:")
for lbl in CRITIQUE_LABELS:
    col = f"weak_{lbl}"
    if col in df.columns:
        n_pos = df[col].sum()
        print(f"    {lbl:40s}  positive: {n_pos:6d}  ({n_pos/len(df)*100:.2f}%)")

none_col = "weak_NONE"
if none_col in df.columns:
    n_none = df[none_col].sum()
    print(f"    {'NONE':40s}  positive: {n_none:6d}  ({n_none/len(df)*100:.2f}%)")

# Report decision paths
if "decision_path" in df.columns:
    paths = df["decision_path"].value_counts()
    print(f"  Decision paths: {dict(paths)}")
if "needs_human_review" in df.columns:
    n_review = df["needs_human_review"].sum()
    print(f"  Flagged for review: {n_review} ({n_review/len(df)*100:.1f}%)")
print(f"  Time: {time.time() - t4:.1f}s")


# ═══════════════════════════════════════════════════════════════════════════
# STAGE 5a: Baseline Training (TF-IDF + Logistic Regression)
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("  STAGE 5a: TF-IDF + Logistic Regression (baseline)")
print("=" * 70)
t5 = time.time()

# Check if we have enough positive examples for training
has_enough_data = True
for lbl in CRITIQUE_LABELS:
    col = f"weak_{lbl}"
    if col in df.columns:
        n_pos = df[col].sum()
        if n_pos < 5:
            print(f"  WARNING: {lbl} has only {n_pos} positive samples")
            has_enough_data = False

if has_enough_data:
    baseline_result = train_tfidf_logreg(df, text_col="clean_text")
    print(f"  Model saved to: {baseline_result['model_dir']}")
    print(f"  Train size: {len(baseline_result['splits']['train_idx'])}")
    print(f"  Val size: {len(baseline_result['splits']['val_idx'])}")
    print(f"  Test size: {len(baseline_result['splits']['test_idx'])}")
else:
    print("  Insufficient positive samples; training anyway with available data...")
    baseline_result = train_tfidf_logreg(df, text_col="clean_text")
    print(f"  Model saved to: {baseline_result['model_dir']}")

print(f"  Time: {time.time() - t5:.1f}s")


# ═══════════════════════════════════════════════════════════════════════════
# STAGE 7: Evaluation (on test split from training)
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("  STAGE 7: Evaluation")
print("=" * 70)
t7 = time.time()

y_test = baseline_result["predictions"]["y_test"]
y_test_pred = baseline_result["predictions"]["y_test_pred"]
y_test_proba = baseline_result["predictions"]["y_test_proba"]

# Get test split dataframe for sliced metrics
test_idx = baseline_result["splits"]["test_idx"]
df_test = df.loc[test_idx].copy()

eval_report = full_evaluation(
    y_true=y_test,
    y_pred=y_test_pred,
    y_proba=y_test_proba,
    df=df_test,
    output_dir=OUTPUT_DIR / "eval",
)

metrics = eval_report["metrics"]
print(f"\n  Micro-F1: {metrics['micro_f1']:.4f}")
print(f"  Macro-F1: {metrics['macro_f1']:.4f}")
print(f"  Micro-Precision: {metrics['micro_precision']:.4f}")
print(f"  Micro-Recall: {metrics['micro_recall']:.4f}")
print()
print("  Per-label metrics:")
for lbl, vals in metrics["per_label"].items():
    print(f"    {lbl:40s}  P={vals['precision']:.3f}  R={vals['recall']:.3f}  F1={vals['f1']:.3f}  support={vals['support']}")

if "optimized_thresholds" in eval_report:
    print("\n  Optimized thresholds:")
    for lbl, thresh in eval_report["optimized_thresholds"].items():
        print(f"    {lbl:40s}  {thresh:.3f}")

if "slice_metrics" in eval_report:
    slices = eval_report["slice_metrics"]
    if "by_text_length" in slices:
        print("\n  By text length:")
        for bucket, vals in slices["by_text_length"].items():
            print(f"    {bucket:25s}  n={vals['count']:6d}  macro-F1={vals['macro_f1']:.4f}")
    if "by_popularity" in slices:
        print("\n  By popularity:")
        for bucket, vals in slices["by_popularity"].items():
            print(f"    {bucket:25s}  n={vals['count']:6d}  macro-F1={vals['macro_f1']:.4f}")

print(f"  Time: {time.time() - t7:.1f}s")


# ═══════════════════════════════════════════════════════════════════════════
# STAGE 6: Ensemble Inference (full dataset)
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("  STAGE 6: Ensemble Inference (full dataset)")
print("=" * 70)
t6 = time.time()

from src.infer import EnsemblePredictor

predictor = EnsemblePredictor(
    rule_miner=miner,
    embedding_retriever=retriever,
    baseline_model_dir=baseline_result["model_dir"],
)

# Inference on original df (predictor runs preprocess internally)
# We need to pass the original text column
df_infer = pd.DataFrame({
    "comment_id": df["comment_id"],
    "text": df["raw_text"],
})
predictions = predictor.predict(df_infer)

# Save predictions
save_jsonl(predictions, OUTPUT_DIR / "predictions.jsonl")
print(f"  Total predictions: {len(predictions)}")

# Summary
label_counts = {}
for lbl in CRITIQUE_LABELS + ["NONE"]:
    label_counts[lbl] = sum(1 for p in predictions if lbl in p["predicted_labels"])
print("\n  Predicted label distribution:")
for lbl, count in sorted(label_counts.items(), key=lambda x: -x[1]):
    print(f"    {lbl:40s}  {count:6d}  ({count/len(predictions)*100:.2f}%)")

n_review = sum(1 for p in predictions if p["needs_human_review"])
print(f"\n  Flagged for human review: {n_review} ({n_review/len(predictions)*100:.1f}%)")

# Save high-confidence detections
critique_detections = [p for p in predictions if "NONE" not in p["predicted_labels"]]
save_jsonl(critique_detections, OUTPUT_DIR / "critique_detections.jsonl")
print(f"  Critique detections saved: {len(critique_detections)}")

print(f"  Time: {time.time() - t6:.1f}s")


# ═══════════════════════════════════════════════════════════════════════════
# STAGE 8: Active Learning
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("  STAGE 8: Active Learning (annotation queue)")
print("=" * 70)
t8 = time.time()

# Use model probs from inference for active learning
model_probs_list = [
    [p["label_probs"].get(lbl, 0.0) for lbl in CRITIQUE_LABELS]
    for p in predictions
]
model_probs_arr = np.array(model_probs_list)

al_df = select_for_annotation(
    df,
    model_probs=model_probs_arr,
    query_size=100,
)
queue_path = export_annotation_queue(al_df, OUTPUT_DIR / "annotation_queue.csv")
print(f"  Selected {len(al_df)} comments for annotation")
print(f"  Queue saved to: {queue_path}")

# Strategy breakdown
if "selection_strategy" in al_df.columns:
    strat_counts = al_df["selection_strategy"].value_counts()
    print(f"  Strategy breakdown: {dict(strat_counts)}")

print(f"  Time: {time.time() - t8:.1f}s")


# ═══════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════
elapsed = time.time() - t_start
print("\n" + "=" * 70)
print("  PIPELINE COMPLETE")
print("=" * 70)
print(f"  Total time: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
print(f"  Comments processed: {len(df)}")
print(f"  Critique detections: {len(critique_detections)}")
print(f"  Flagged for review: {n_review}")
print()
print("  Output files:")
print(f"    {OUTPUT_DIR / 'predictions.jsonl'}")
print(f"    {OUTPUT_DIR / 'critique_detections.jsonl'}")
print(f"    {OUTPUT_DIR / 'rule_coverage_report.json'}")
print(f"    {OUTPUT_DIR / 'annotation_queue.csv'}")
print(f"    {OUTPUT_DIR / 'eval/metrics.json'}")
print(f"    {OUTPUT_DIR / 'eval/pr_curves.json'}")
print(f"    {OUTPUT_DIR / 'eval/optimized_thresholds.json'}")
print(f"    {OUTPUT_DIR / 'eval/data_profile.json'}")
