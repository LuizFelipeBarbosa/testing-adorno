"""Inference module — run the full ensemble pipeline on new comments.

Produces JSONL output with the contracted schema:
- comment_id, raw_text, predicted_labels, label_probs, evidence,
  decision_path, needs_human_review
"""

from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

from src.preprocess import preprocess_dataframe
from src.rule_miner import RuleMiner
from src.embed_retrieval import EmbeddingRetriever
from src.utils.io_utils import (
    load_yaml,
    save_jsonl,
    ensure_dir,
    project_root,
)
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


class EnsemblePredictor:
    """Combines rule, embedding, and model signals for final prediction."""

    def __init__(
        self,
        rule_miner: RuleMiner | None = None,
        embedding_retriever: EmbeddingRetriever | None = None,
        baseline_model_dir: str | Path | None = None,
        transformer_model_dir: str | Path | None = None,
        config_path: str | Path | None = None,
    ):
        self.config = load_yaml(
            config_path or project_root() / "configs" / "model_config.yaml"
        )
        self.thresholds_cfg = load_yaml(
            project_root() / "configs" / "thresholds.yaml"
        )
        self.thresholds = self.thresholds_cfg.get("thresholds", {})
        self.ensemble_cfg = self.config.get("ensemble", {})
        self.human_review_cfg = self.thresholds_cfg.get("human_review", {})

        self.rule_miner = rule_miner or RuleMiner()
        self.embedding_retriever = embedding_retriever
        self._baseline_vectorizer = None
        self._baseline_classifier = None
        self._transformer_model = None
        self._transformer_tokenizer = None

        # Load baseline if available
        if baseline_model_dir and Path(baseline_model_dir).exists():
            from src.train_baseline import load_baseline_model

            self._baseline_vectorizer, self._baseline_classifier = load_baseline_model(
                baseline_model_dir
            )
            logger.info("Loaded baseline model from %s", baseline_model_dir)

        # Load transformer if available
        if transformer_model_dir and Path(transformer_model_dir).exists():
            from src.train_transformer import load_transformer_model

            self._transformer_model, self._transformer_tokenizer = (
                load_transformer_model(transformer_model_dir)
            )
            logger.info("Loaded transformer model from %s", transformer_model_dir)

    def _get_model_probs(self, texts: list[str]) -> np.ndarray | None:
        """Get model probability predictions."""
        if self._transformer_model is not None:
            return self._predict_transformer(texts)
        elif self._baseline_classifier is not None:
            return self._predict_baseline(texts)
        return None

    def _predict_baseline(self, texts: list[str]) -> np.ndarray:
        """Predict with the baseline TF-IDF model."""
        X = self._baseline_vectorizer.transform(texts)
        return self._baseline_classifier.predict_proba(X)

    def _predict_transformer(self, texts: list[str]) -> np.ndarray:
        """Predict with the transformer model."""
        import torch

        model = self._transformer_model
        tokenizer = self._transformer_tokenizer
        device = next(model.parameters()).device
        max_len = self.config["transformer"]["max_length"]
        batch_size = self.config["transformer"]["batch_size"]

        all_probs = []
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            encoding = tokenizer(
                batch_texts,
                max_length=max_len,
                padding="max_length",
                truncation=True,
                return_tensors="pt",
            ).to(device)

            with torch.no_grad():
                logits = model(**encoding)
                probs = torch.sigmoid(logits).cpu().numpy()
            all_probs.append(probs)

        return np.concatenate(all_probs, axis=0)

    def predict(
        self,
        df: pd.DataFrame,
        text_col: str = "text",
    ) -> list[dict[str, Any]]:
        """Run full ensemble prediction pipeline.

        Args:
            df: DataFrame with at least a text column.
            text_col: Column containing comment text.

        Returns:
            List of dicts matching the output contract.
        """
        # Stage 1: Preprocess
        df = preprocess_dataframe(df, text_col=text_col)

        # Stage 2: Rules
        df = self.rule_miner.match_dataframe(df, text_col="clean_text")

        # Stage 3: Embeddings (if available)
        if self.embedding_retriever:
            df = self.embedding_retriever.match_dataframe(df, text_col="clean_text")

        # Stage 5: Model probabilities
        texts = df["clean_text"].fillna("").tolist()
        model_probs = self._get_model_probs(texts)

        # Stage 6: Ensemble
        results: list[dict[str, Any]] = []
        rule_w = self.ensemble_cfg.get("rule_weight", 0.25)
        emb_w = self.ensemble_cfg.get("embedding_weight", 0.25)
        model_w = self.ensemble_cfg.get("model_weight", 0.50)

        for idx, (_, row) in enumerate(df.iterrows()):
            comment_id = str(row.get("comment_id", idx))
            raw_text = str(row.get("raw_text", row.get(text_col, "")))

            label_probs: dict[str, float] = {}
            evidence: dict[str, str] = {}
            decision_paths: dict[str, str] = {}

            for i, lbl in enumerate(CRITIQUE_LABELS):
                # Rule signal
                rule_hit = bool(row.get(f"rule_{lbl}", False))
                rule_conf = float(row.get(f"rule_{lbl}_conf", 0.0))
                rule_spans = row.get(f"rule_{lbl}_spans", [])

                # Embedding signal
                emb_score = float(row.get(f"emb_{lbl}_score", 0.0))
                emb_proto = row.get(f"emb_{lbl}_prototype", "")

                # Model signal
                m_prob = float(model_probs[idx, i]) if model_probs is not None else 0.0

                # Combine
                if model_probs is not None:
                    rule_signal = rule_conf if rule_hit else 0.05
                    combined = (
                        rule_signal * rule_w + emb_score * emb_w + m_prob * model_w
                    ) / (rule_w + emb_w + model_w)
                    path = "ensemble"
                elif self.embedding_retriever:
                    rule_signal = rule_conf if rule_hit else 0.05
                    combined = (rule_signal + emb_score) / 2.0
                    path = "rule+embedding"
                else:
                    combined = rule_conf if rule_hit else 0.05
                    path = "rule"

                label_probs[lbl] = round(float(np.clip(combined, 0.0, 1.0)), 4)
                decision_paths[lbl] = path

                # Evidence selection
                if rule_hit and rule_spans:
                    spans = rule_spans if isinstance(rule_spans, list) else []
                    if spans:
                        evidence[lbl] = f"rule match: '{spans[0][2] if len(spans[0]) > 2 else ''}'"
                    else:
                        evidence[lbl] = "rule match"
                elif emb_score > 0.5 and emb_proto:
                    evidence[lbl] = f"similar to prototype: '{emb_proto[:80]}...'"
                elif m_prob > 0.5:
                    evidence[lbl] = "model prediction"
                else:
                    evidence[lbl] = ""

            # Apply thresholds
            predicted_labels = []
            for lbl in CRITIQUE_LABELS:
                thresh = self.thresholds.get(lbl, 0.50)
                if label_probs[lbl] >= thresh:
                    predicted_labels.append(lbl)

            if not predicted_labels:
                predicted_labels = ["NONE"]

            # Determine human review need
            max_prob = max(label_probs.values())
            entropy = self._compute_entropy(label_probs)
            max_conf_thresh = self.human_review_cfg.get("max_confidence_for_review", 0.65)
            ent_thresh = self.human_review_cfg.get("entropy_threshold", 0.70)
            needs_review = max_prob < max_conf_thresh or entropy > ent_thresh

            # Determine overall decision path
            if model_probs is not None:
                overall_path = "ensemble"
            elif self.embedding_retriever:
                overall_path = "rule+embedding"
            else:
                overall_path = "rule"

            results.append({
                "comment_id": comment_id,
                "raw_text": raw_text,
                "predicted_labels": predicted_labels,
                "label_probs": label_probs,
                "evidence": evidence,
                "decision_path": overall_path,
                "needs_human_review": needs_review,
            })

        logger.info(
            "Inference complete: %d comments, %d flagged for review",
            len(results),
            sum(1 for r in results if r["needs_human_review"]),
        )
        return results

    @staticmethod
    def _compute_entropy(probs: dict[str, float]) -> float:
        """Compute mean binary entropy across label probabilities."""
        eps = 1e-10
        total = 0.0
        for p in probs.values():
            p = max(min(p, 1.0 - eps), eps)
            total += -(p * np.log2(p) + (1 - p) * np.log2(1 - p))
        return total / max(len(probs), 1)


def run_inference(
    input_path: str | Path,
    output_path: str | Path | None = None,
    baseline_model_dir: str | Path | None = None,
    transformer_model_dir: str | Path | None = None,
    use_embeddings: bool = True,
) -> list[dict[str, Any]]:
    """Run inference on a file and save JSONL output.

    Args:
        input_path: Path to input CSV/JSON/JSONL.
        output_path: Path for output JSONL (default: outputs/predictions.jsonl).
        baseline_model_dir: Path to saved baseline model.
        transformer_model_dir: Path to saved transformer model.
        use_embeddings: Whether to use embedding retrieval.

    Returns:
        List of prediction dicts.
    """
    from src.data_ingest import ingest

    df = ingest(input_path)

    embedding_retriever = None
    if use_embeddings:
        embedding_retriever = EmbeddingRetriever()

    predictor = EnsemblePredictor(
        baseline_model_dir=baseline_model_dir,
        transformer_model_dir=transformer_model_dir,
        embedding_retriever=embedding_retriever,
    )

    results = predictor.predict(df)

    out = Path(output_path or project_root() / "outputs" / "predictions.jsonl")
    save_jsonl(results, out)
    logger.info("Saved %d predictions to %s", len(results), out)

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run critique detection inference")
    parser.add_argument("input", help="Path to input CSV/JSON/JSONL")
    parser.add_argument("-o", "--output", help="Output JSONL path")
    parser.add_argument("--baseline-model", help="Path to baseline model directory")
    parser.add_argument("--transformer-model", help="Path to transformer model directory")
    parser.add_argument("--no-embeddings", action="store_true", help="Disable embeddings")
    args = parser.parse_args()

    run_inference(
        args.input,
        output_path=args.output,
        baseline_model_dir=args.baseline_model,
        transformer_model_dir=args.transformer_model,
        use_embeddings=not args.no_embeddings,
    )
