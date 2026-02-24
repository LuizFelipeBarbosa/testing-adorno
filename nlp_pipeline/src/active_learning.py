"""Stage 8: Active learning — uncertainty sampling and annotation queue.

Implements three query strategies:
1. Entropy-based: select comments with highest prediction entropy.
2. Near-threshold: select comments closest to decision boundaries.
3. Disagreement: select comments where rules vs model vs LLM disagree.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

from src.utils.io_utils import ensure_dir, project_root
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


def _binary_entropy(p: float) -> float:
    """Compute binary entropy H(p) = -p*log2(p) - (1-p)*log2(1-p)."""
    eps = 1e-10
    p = max(min(p, 1.0 - eps), eps)
    return -(p * np.log2(p) + (1 - p) * np.log2(1 - p))


def entropy_scores(probs: np.ndarray) -> np.ndarray:
    """Compute mean binary entropy across labels for each sample.

    Args:
        probs: shape (n_samples, n_labels), values in [0, 1].

    Returns:
        shape (n_samples,) with mean entropy per sample.
    """
    ent = np.vectorize(_binary_entropy)(probs)
    return ent.mean(axis=1)


def near_threshold_scores(
    probs: np.ndarray,
    thresholds: dict[str, float] | None = None,
    default_threshold: float = 0.50,
) -> np.ndarray:
    """Score samples by proximity to decision thresholds.

    Closer to threshold => higher score (more informative).
    """
    thresh_arr = np.array([
        thresholds.get(lbl, default_threshold) if thresholds else default_threshold
        for lbl in CRITIQUE_LABELS
    ])
    distances = np.abs(probs - thresh_arr)
    # Invert: smaller distance = higher score. Use min distance across labels.
    min_dist = distances.min(axis=1)
    return 1.0 - min_dist


def disagreement_scores(
    df: pd.DataFrame,
    model_probs: np.ndarray | None = None,
    threshold: float = 0.50,
) -> np.ndarray:
    """Score samples by disagreement between rule-based and model predictions.

    Higher score = more disagreement across sources.
    """
    n = len(df)
    scores = np.zeros(n)

    for i, lbl in enumerate(CRITIQUE_LABELS):
        rule_col = f"rule_{lbl}"
        if rule_col not in df.columns:
            continue

        rule_pred = df[rule_col].astype(int).values

        if model_probs is not None:
            model_pred = (model_probs[:, i] >= threshold).astype(int)
            scores += (rule_pred != model_pred).astype(float)

        # Check embedding signals
        emb_col = f"emb_{lbl}_score"
        if emb_col in df.columns:
            emb_pred = (df[emb_col].values >= 0.45).astype(int)
            scores += (rule_pred != emb_pred).astype(float)
            if model_probs is not None:
                scores += (model_pred != emb_pred).astype(float)

    return scores


def select_for_annotation(
    df: pd.DataFrame,
    model_probs: np.ndarray | None = None,
    strategies: list[str] | None = None,
    query_size: int = 50,
    thresholds: dict[str, float] | None = None,
    entropy_percentile: float = 90.0,
) -> pd.DataFrame:
    """Select comments for human annotation using active learning.

    Args:
        df: DataFrame with rule/embedding features and text.
        model_probs: Model probability predictions (n_samples, n_labels).
        strategies: List of strategies to use. Default: all three.
        query_size: Total number of samples to select.
        thresholds: Per-label thresholds for near_threshold strategy.
        entropy_percentile: Percentile for entropy filtering.

    Returns:
        DataFrame of selected samples with annotation metadata.
    """
    strategies = strategies or ["entropy", "near_threshold", "disagreement"]
    per_strategy = max(query_size // len(strategies), 1)

    selected_indices: set[int] = set()
    selection_reasons: dict[int, str] = {}

    # Build probability matrix from available sources
    if model_probs is not None:
        probs = model_probs
    else:
        # Fall back to weak label probabilities
        prob_cols = [f"weak_{lbl}_prob" for lbl in CRITIQUE_LABELS]
        available = [c for c in prob_cols if c in df.columns]
        if available:
            probs = df[available].values
        else:
            # Last resort: embedding scores
            emb_cols = [f"emb_{lbl}_score" for lbl in CRITIQUE_LABELS]
            available = [c for c in emb_cols if c in df.columns]
            if available:
                probs = df[available].values
            else:
                logger.warning("No probability columns available for active learning")
                return df.head(0)

    if "entropy" in strategies:
        ent = entropy_scores(probs)
        cutoff = np.percentile(ent, entropy_percentile)
        high_ent = np.where(ent >= cutoff)[0]
        chosen = np.random.choice(
            high_ent, size=min(per_strategy, len(high_ent)), replace=False
        )
        for idx in chosen:
            selected_indices.add(int(idx))
            selection_reasons[int(idx)] = "entropy"

    if "near_threshold" in strategies:
        nt = near_threshold_scores(probs, thresholds)
        top_nt = np.argsort(nt)[::-1]
        count = 0
        for idx in top_nt:
            idx = int(idx)
            if idx not in selected_indices:
                selected_indices.add(idx)
                selection_reasons[idx] = "near_threshold"
                count += 1
                if count >= per_strategy:
                    break

    if "disagreement" in strategies:
        disagree = disagreement_scores(df, model_probs)
        top_dis = np.argsort(disagree)[::-1]
        count = 0
        for idx in top_dis:
            idx = int(idx)
            if idx not in selected_indices:
                selected_indices.add(idx)
                selection_reasons[idx] = "disagreement"
                count += 1
                if count >= per_strategy:
                    break

    selected_idx = sorted(selected_indices)
    result = df.iloc[selected_idx].copy()
    result["selection_strategy"] = [selection_reasons[i] for i in selected_idx]

    # Add annotation columns
    for lbl in CRITIQUE_LABELS:
        result[f"human_{lbl}"] = ""
    result["annotator_notes"] = ""

    logger.info(
        "Selected %d samples for annotation: %s",
        len(result),
        {s: list(selection_reasons.values()).count(s) for s in strategies},
    )

    return result


def export_annotation_queue(
    df: pd.DataFrame,
    output_path: str | Path | None = None,
    text_col: str = "raw_text",
    include_signals: bool = True,
) -> Path:
    """Export annotation queue as CSV for human review.

    Args:
        df: Selected samples from select_for_annotation().
        output_path: Path for the CSV file.
        text_col: Column name for the comment text.
        include_signals: Whether to include rule/embedding columns.

    Returns:
        Path to the exported CSV.
    """
    path = Path(
        output_path or project_root() / "outputs" / "annotation_queue.csv"
    )
    ensure_dir(path.parent)

    # Select columns for export
    base_cols = ["comment_id", text_col, "selection_strategy"]
    human_cols = [f"human_{lbl}" for lbl in CRITIQUE_LABELS] + ["annotator_notes"]

    signal_cols = []
    if include_signals:
        for lbl in CRITIQUE_LABELS:
            for prefix in ["rule_", "emb_", "weak_"]:
                col = f"{prefix}{lbl}"
                if col in df.columns:
                    signal_cols.append(col)
                conf_col = f"{prefix}{lbl}_conf"
                if conf_col in df.columns:
                    signal_cols.append(conf_col)
                score_col = f"{prefix}{lbl}_score"
                if score_col in df.columns:
                    signal_cols.append(score_col)

    all_cols = [c for c in base_cols + signal_cols + human_cols if c in df.columns]
    export_df = df[all_cols].copy()
    export_df.to_csv(path, index=False, encoding="utf-8")

    logger.info("Exported %d items to %s", len(export_df), path)
    return path
