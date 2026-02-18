"""Stage 7: Evaluation — metrics, PR curves, confusion, and sliced analysis.

Computes micro/macro F1, per-label precision/recall/F1, PR curves,
confusion/co-occurrence matrices, and slice metrics.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd
from sklearn.metrics import (
    classification_report,
    f1_score,
    precision_recall_curve,
    average_precision_score,
    multilabel_confusion_matrix,
    precision_score,
    recall_score,
)

from src.utils.io_utils import save_json, ensure_dir, project_root
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

CRITIQUE_LABELS = [
    "STANDARDIZATION",
    "PSEUDO_INDIVIDUALIZATION",
    "COMMODIFICATION_MARKET_LOGIC",
    "REGRESSIVE_LISTENING",
    "AFFECTIVE_PREPACKAGING",
    "FORMAL_RESISTANCE",
]


def compute_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_proba: np.ndarray | None = None,
    label_names: list[str] | None = None,
) -> dict[str, Any]:
    """Compute comprehensive multi-label metrics.

    Args:
        y_true: Binary ground truth matrix (n_samples, n_labels).
        y_pred: Binary prediction matrix.
        y_proba: Probability matrix (optional, for PR curves).
        label_names: Names for each label column.

    Returns:
        Dict with per-label and aggregate metrics.
    """
    names = label_names or CRITIQUE_LABELS
    n_labels = y_true.shape[1]
    assert len(names) == n_labels, f"Label count mismatch: {len(names)} vs {n_labels}"

    results: dict[str, Any] = {}

    # Aggregate metrics
    results["micro_f1"] = float(f1_score(y_true, y_pred, average="micro", zero_division=0))
    results["macro_f1"] = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
    results["micro_precision"] = float(
        precision_score(y_true, y_pred, average="micro", zero_division=0)
    )
    results["micro_recall"] = float(
        recall_score(y_true, y_pred, average="micro", zero_division=0)
    )
    results["macro_precision"] = float(
        precision_score(y_true, y_pred, average="macro", zero_division=0)
    )
    results["macro_recall"] = float(
        recall_score(y_true, y_pred, average="macro", zero_division=0)
    )

    # Per-label metrics
    per_label: dict[str, dict[str, float]] = {}
    for i, name in enumerate(names):
        tp = int(((y_true[:, i] == 1) & (y_pred[:, i] == 1)).sum())
        fp = int(((y_true[:, i] == 0) & (y_pred[:, i] == 1)).sum())
        fn = int(((y_true[:, i] == 1) & (y_pred[:, i] == 0)).sum())
        tn = int(((y_true[:, i] == 0) & (y_pred[:, i] == 0)).sum())

        precision = tp / max(tp + fp, 1)
        recall = tp / max(tp + fn, 1)
        f1 = 2 * precision * recall / max(precision + recall, 1e-10)

        entry = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "support": int(y_true[:, i].sum()),
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn,
        }

        if y_proba is not None:
            entry["avg_precision"] = round(
                float(average_precision_score(y_true[:, i], y_proba[:, i])), 4
            )

        per_label[name] = entry

    results["per_label"] = per_label

    # Co-occurrence matrix (which labels tend to co-occur in predictions)
    cooccurrence = (y_pred.T @ y_pred).tolist()
    results["cooccurrence_matrix"] = {
        "labels": names,
        "matrix": cooccurrence,
    }

    return results


def compute_pr_curves(
    y_true: np.ndarray,
    y_proba: np.ndarray,
    label_names: list[str] | None = None,
) -> dict[str, dict[str, list[float]]]:
    """Compute precision-recall curves per label."""
    names = label_names or CRITIQUE_LABELS
    curves: dict[str, dict[str, list[float]]] = {}

    for i, name in enumerate(names):
        precision, recall, thresholds = precision_recall_curve(
            y_true[:, i], y_proba[:, i]
        )
        curves[name] = {
            "precision": precision.tolist(),
            "recall": recall.tolist(),
            "thresholds": thresholds.tolist(),
        }

    return curves


def optimize_thresholds(
    y_true: np.ndarray,
    y_proba: np.ndarray,
    label_names: list[str] | None = None,
    metric: str = "f1",
    search_range: tuple[float, float] = (0.20, 0.80),
    search_step: float = 0.01,
    min_precision: float = 0.60,
) -> dict[str, float]:
    """Find optimal threshold per label on a validation set.

    Returns dict mapping label name to optimal threshold.
    """
    names = label_names or CRITIQUE_LABELS
    thresholds: dict[str, float] = {}

    for i, name in enumerate(names):
        best_thresh = 0.50
        best_score = -1.0

        for t in np.arange(search_range[0], search_range[1] + search_step, search_step):
            preds = (y_proba[:, i] >= t).astype(int)
            tp = ((y_true[:, i] == 1) & (preds == 1)).sum()
            fp = ((y_true[:, i] == 0) & (preds == 1)).sum()
            fn = ((y_true[:, i] == 1) & (preds == 0)).sum()

            prec = tp / max(tp + fp, 1)
            rec = tp / max(tp + fn, 1)

            if prec < min_precision:
                continue

            if metric == "f1":
                score = 2 * prec * rec / max(prec + rec, 1e-10)
            elif metric == "precision":
                score = prec
            elif metric == "recall":
                score = rec
            else:
                score = 2 * prec * rec / max(prec + rec, 1e-10)

            if score > best_score:
                best_score = score
                best_thresh = float(t)

        thresholds[name] = round(best_thresh, 3)
        logger.info("Optimal threshold for %s: %.3f (score=%.4f)", name, best_thresh, best_score)

    return thresholds


def slice_metrics(
    df: pd.DataFrame,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    label_names: list[str] | None = None,
) -> dict[str, Any]:
    """Compute metrics sliced by language, comment length, and popularity.

    Expects df to have columns: language, text_length, like_count (optional).
    """
    names = label_names or CRITIQUE_LABELS
    slices: dict[str, Any] = {}

    # By language
    if "language" in df.columns:
        lang_metrics = {}
        for lang in df["language"].unique():
            mask = (df["language"] == lang).values
            if mask.sum() < 10:
                continue
            lang_metrics[lang] = {
                "count": int(mask.sum()),
                "macro_f1": round(
                    float(f1_score(y_true[mask], y_pred[mask], average="macro", zero_division=0)),
                    4,
                ),
            }
        slices["by_language"] = lang_metrics

    # By text length buckets
    if "text_length" in df.columns:
        bins = [0, 50, 150, 500, float("inf")]
        bucket_names = ["short(0-50)", "medium(50-150)", "long(150-500)", "very_long(500+)"]
        length_metrics = {}
        for bname, lo, hi in zip(bucket_names, bins[:-1], bins[1:]):
            mask = ((df["text_length"] >= lo) & (df["text_length"] < hi)).values
            if mask.sum() < 10:
                continue
            length_metrics[bname] = {
                "count": int(mask.sum()),
                "macro_f1": round(
                    float(f1_score(y_true[mask], y_pred[mask], average="macro", zero_division=0)),
                    4,
                ),
            }
        slices["by_text_length"] = length_metrics

    # By popularity (like_count)
    if "like_count" in df.columns:
        like_col = pd.to_numeric(df["like_count"], errors="coerce").fillna(0)
        bins = [0, 5, 50, 500, float("inf")]
        bucket_names = ["low(0-5)", "medium(5-50)", "high(50-500)", "viral(500+)"]
        pop_metrics = {}
        for bname, lo, hi in zip(bucket_names, bins[:-1], bins[1:]):
            mask = ((like_col >= lo) & (like_col < hi)).values
            if mask.sum() < 10:
                continue
            pop_metrics[bname] = {
                "count": int(mask.sum()),
                "macro_f1": round(
                    float(f1_score(y_true[mask], y_pred[mask], average="macro", zero_division=0)),
                    4,
                ),
            }
        slices["by_popularity"] = pop_metrics

    return slices


def full_evaluation(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_proba: np.ndarray | None = None,
    df: pd.DataFrame | None = None,
    label_names: list[str] | None = None,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Run full evaluation suite and optionally save results."""
    report: dict[str, Any] = {}

    report["metrics"] = compute_metrics(y_true, y_pred, y_proba, label_names)

    if y_proba is not None:
        report["pr_curves"] = compute_pr_curves(y_true, y_proba, label_names)
        report["optimized_thresholds"] = optimize_thresholds(
            y_true, y_proba, label_names
        )

    if df is not None:
        report["slice_metrics"] = slice_metrics(df, y_true, y_pred, label_names)

    if output_dir:
        out = Path(output_dir)
        ensure_dir(out)
        save_json(report["metrics"], out / "metrics.json")
        if "pr_curves" in report:
            save_json(report["pr_curves"], out / "pr_curves.json")
        if "optimized_thresholds" in report:
            save_json(report["optimized_thresholds"], out / "optimized_thresholds.json")
        if "slice_metrics" in report:
            save_json(report["slice_metrics"], out / "slice_metrics.json")
        logger.info("Evaluation results saved to %s", out)

    # Log summary
    m = report["metrics"]
    logger.info("Micro-F1: %.4f | Macro-F1: %.4f", m["micro_f1"], m["macro_f1"])
    for name, vals in m["per_label"].items():
        logger.info(
            "  %s: P=%.3f R=%.3f F1=%.3f (support=%d)",
            name,
            vals["precision"],
            vals["recall"],
            vals["f1"],
            vals["support"],
        )

    return report
