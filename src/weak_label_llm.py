"""Stage 4: Weak supervision + LLM adjudication.

Combines rule-based and embedding signals to produce candidate labels.
For ambiguous / high-entropy cases, calls an LLM with a strict JSON schema
for final adjudication.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np
import pandas as pd

from src.prompts.adjudication import (
    SYSTEM_PROMPT,
    REPAIR_PROMPT,
    format_adjudication_prompt,
)
from src.utils.io_utils import load_yaml, project_root
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


@dataclass
class WeakLabel:
    """Combined weak label for a single comment."""

    comment_id: str
    rule_labels: dict[str, bool] = field(default_factory=dict)
    rule_confidences: dict[str, float] = field(default_factory=dict)
    embedding_scores: dict[str, float] = field(default_factory=dict)
    llm_labels: dict[str, bool] | None = None
    llm_evidence: dict[str, str] | None = None
    llm_notes: str = ""
    combined_labels: dict[str, bool] = field(default_factory=dict)
    combined_probs: dict[str, float] = field(default_factory=dict)
    decision_path: str = ""
    needs_human_review: bool = False
    entropy: float = 0.0


def compute_entropy(probs: dict[str, float]) -> float:
    """Compute binary entropy over independent label probabilities."""
    eps = 1e-10
    total = 0.0
    for p in probs.values():
        p = max(min(p, 1.0 - eps), eps)
        total += -(p * np.log2(p) + (1 - p) * np.log2(1 - p))
    return float(total / max(len(probs), 1))


def combine_signals(
    rule_hit: bool,
    rule_conf: float,
    emb_score: float,
    rule_weight: float = 0.25,
    emb_weight: float = 0.25,
    base_weight: float = 0.50,
) -> float:
    """Combine rule and embedding signals into a single probability.

    When no model probability is available yet, the base_weight portion
    is distributed between rule and embedding proportionally.
    """
    # Rule signal: either the confidence prior or a low baseline
    rule_signal = rule_conf if rule_hit else 0.05
    # Redistribute base_weight evenly for pre-model stage
    effective_rule_w = rule_weight + base_weight * 0.5
    effective_emb_w = emb_weight + base_weight * 0.5
    total_w = effective_rule_w + effective_emb_w

    combined = (rule_signal * effective_rule_w + emb_score * effective_emb_w) / total_w
    return float(np.clip(combined, 0.0, 1.0))


def _parse_llm_response(response_text: str) -> dict[str, Any] | None:
    """Parse and validate the LLM JSON response."""
    # Try to extract JSON from the response
    text = response_text.strip()
    # Handle markdown code blocks
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]) if len(lines) > 2 else text

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON in the response
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                data = json.loads(text[start:end])
            except json.JSONDecodeError:
                return None
        else:
            return None

    # Validate structure
    if "labels" not in data:
        return None

    labels = data["labels"]
    for lbl in CRITIQUE_LABELS + ["NONE"]:
        if lbl not in labels:
            return None
        entry = labels[lbl]
        if not isinstance(entry, dict) or "value" not in entry:
            return None

    return data


def _enforce_none_policy(labels: dict[str, bool]) -> dict[str, bool]:
    """Ensure NONE is true IFF all critique labels are false."""
    any_critique = any(labels.get(lbl, False) for lbl in CRITIQUE_LABELS)
    labels["NONE"] = not any_critique
    return labels


class WeakLabeler:
    """Combines rule + embedding signals and optionally invokes LLM."""

    def __init__(
        self,
        config_path: str | None = None,
        api_key: str | None = None,
    ):
        config_file = config_path or str(
            project_root() / "configs" / "model_config.yaml"
        )
        self.config = load_yaml(config_file)
        self.llm_config = self.config.get("llm", {})
        self.ensemble_config = self.config.get("ensemble", {})

        self.entropy_threshold = self.llm_config.get("entropy_threshold", 0.70)
        self.disagreement_threshold = self.llm_config.get("disagreement_threshold", 2)
        self.max_retries = self.llm_config.get("max_retries", 1)

        self.rule_weight = self.ensemble_config.get("rule_weight", 0.25)
        self.emb_weight = self.ensemble_config.get("embedding_weight", 0.25)
        self.model_weight = self.ensemble_config.get("model_weight", 0.50)

        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self._client = None

    @property
    def client(self):
        """Lazy-initialize the Anthropic client."""
        if self._client is None:
            if not self._api_key:
                raise ValueError(
                    "ANTHROPIC_API_KEY is required for LLM adjudication. "
                    "Set it as an environment variable or pass api_key."
                )
            try:
                import anthropic

                self._client = anthropic.Anthropic(api_key=self._api_key)
            except ImportError:
                raise ImportError(
                    "anthropic is required for LLM adjudication. "
                    "Install with: pip install anthropic"
                )
        return self._client

    def _call_llm(self, prompt: str) -> str | None:
        """Call the LLM API and return the response text."""
        try:
            response = self.client.messages.create(
                model=self.llm_config.get("model", "claude-sonnet-4-20250514"),
                max_tokens=self.llm_config.get("max_tokens", 1024),
                temperature=self.llm_config.get("temperature", 0.0),
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        except Exception as e:
            logger.error("LLM API call failed: %s", e)
            return None

    def adjudicate_single(
        self,
        comment: str,
        rule_hits: dict[str, bool],
        embedding_scores: dict[str, float],
    ) -> dict[str, Any] | None:
        """Call LLM to adjudicate a single ambiguous comment."""
        prompt = format_adjudication_prompt(comment, rule_hits, embedding_scores)

        response_text = self._call_llm(prompt)
        if response_text is None:
            return None

        parsed = _parse_llm_response(response_text)
        if parsed is not None:
            return parsed

        # Retry with repair prompt
        if self.max_retries > 0:
            logger.warning("Invalid LLM JSON, attempting repair...")
            repair = REPAIR_PROMPT.format(previous_response=response_text)
            repair_text = self._call_llm(repair)
            if repair_text:
                parsed = _parse_llm_response(repair_text)
                if parsed is not None:
                    return parsed

        logger.error("LLM adjudication failed after retries")
        return None

    def label_single(
        self,
        comment_id: str,
        text: str,
        rule_hits: dict[str, bool],
        rule_confs: dict[str, float],
        emb_scores: dict[str, float],
        use_llm: bool = True,
    ) -> WeakLabel:
        """Produce a weak label for a single comment."""
        # Combine rule + embedding signals
        combined_probs = {}
        for lbl in CRITIQUE_LABELS:
            combined_probs[lbl] = combine_signals(
                rule_hit=rule_hits.get(lbl, False),
                rule_conf=rule_confs.get(lbl, 0.0),
                emb_score=emb_scores.get(lbl, 0.0),
                rule_weight=self.rule_weight,
                emb_weight=self.emb_weight,
                base_weight=self.model_weight,
            )

        entropy = compute_entropy(combined_probs)

        # Check for disagreement between sources
        disagreements = 0
        for lbl in CRITIQUE_LABELS:
            rule_says = rule_hits.get(lbl, False)
            emb_says = emb_scores.get(lbl, 0.0) > 0.5
            if rule_says != emb_says:
                disagreements += 1

        needs_llm = (
            use_llm
            and self._api_key
            and (
                entropy > self.entropy_threshold
                or disagreements >= self.disagreement_threshold
            )
        )

        wl = WeakLabel(
            comment_id=comment_id,
            rule_labels=rule_hits,
            rule_confidences=rule_confs,
            embedding_scores=emb_scores,
            combined_probs=combined_probs,
            entropy=entropy,
        )

        if needs_llm:
            logger.debug(
                "Routing to LLM: comment_id=%s entropy=%.3f disagreements=%d",
                comment_id,
                entropy,
                disagreements,
            )
            llm_result = self.adjudicate_single(text, rule_hits, emb_scores)
            if llm_result:
                llm_labels_raw = {
                    lbl: llm_result["labels"][lbl]["value"]
                    for lbl in CRITIQUE_LABELS + ["NONE"]
                }
                wl.llm_labels = _enforce_none_policy(llm_labels_raw)
                wl.llm_evidence = {
                    lbl: llm_result["labels"][lbl].get("evidence", "")
                    for lbl in CRITIQUE_LABELS
                }
                wl.llm_notes = llm_result.get("notes", "")
                wl.decision_path = "llm"

                # Override combined probs with LLM verdict
                for lbl in CRITIQUE_LABELS:
                    if wl.llm_labels[lbl]:
                        wl.combined_probs[lbl] = max(wl.combined_probs[lbl], 0.85)
                    else:
                        wl.combined_probs[lbl] = min(wl.combined_probs[lbl], 0.20)
            else:
                wl.needs_human_review = True
                wl.decision_path = "rule+embedding (llm_failed)"
        else:
            wl.decision_path = "rule+embedding"

        # Determine final labels from combined probs
        thresholds_cfg = load_yaml(project_root() / "configs" / "thresholds.yaml")
        thresholds = thresholds_cfg.get("thresholds", {})
        for lbl in CRITIQUE_LABELS:
            thresh = thresholds.get(lbl, 0.50)
            wl.combined_labels[lbl] = wl.combined_probs[lbl] >= thresh
        wl.combined_labels = _enforce_none_policy(wl.combined_labels)

        # Flag for human review if still high entropy
        if entropy > self.entropy_threshold and not needs_llm:
            wl.needs_human_review = True

        return wl

    def label_dataframe(
        self,
        df: pd.DataFrame,
        use_llm: bool = False,
        llm_budget: int = 100,
    ) -> pd.DataFrame:
        """Produce weak labels for an entire DataFrame.

        Args:
            df: DataFrame with rule and embedding columns already added.
            use_llm: Whether to use LLM for ambiguous cases.
            llm_budget: Maximum number of LLM calls to make.
        """
        llm_calls = 0
        results: list[dict] = []

        for _, row in df.iterrows():
            comment_id = str(row.get("comment_id", ""))
            text = str(row.get("clean_text", row.get("text", "")))

            # Gather rule signals
            rule_hits = {}
            rule_confs = {}
            for lbl in CRITIQUE_LABELS:
                rule_hits[lbl] = bool(row.get(f"rule_{lbl}", False))
                rule_confs[lbl] = float(row.get(f"rule_{lbl}_conf", 0.0))

            # Gather embedding signals
            emb_scores = {}
            for lbl in CRITIQUE_LABELS:
                emb_scores[lbl] = float(row.get(f"emb_{lbl}_score", 0.0))

            should_use_llm = use_llm and llm_calls < llm_budget
            wl = self.label_single(
                comment_id=comment_id,
                text=text,
                rule_hits=rule_hits,
                rule_confs=rule_confs,
                emb_scores=emb_scores,
                use_llm=should_use_llm,
            )

            if wl.decision_path == "llm":
                llm_calls += 1

            record = {
                "comment_id": comment_id,
                "entropy": wl.entropy,
                "decision_path": wl.decision_path,
                "needs_human_review": wl.needs_human_review,
            }
            for lbl in CRITIQUE_LABELS:
                record[f"weak_{lbl}"] = wl.combined_labels.get(lbl, False)
                record[f"weak_{lbl}_prob"] = wl.combined_probs.get(lbl, 0.0)
            record["weak_NONE"] = wl.combined_labels.get("NONE", True)
            results.append(record)

        result_df = pd.DataFrame(results)
        logger.info(
            "Weak labeling complete: %d comments, %d LLM calls",
            len(result_df),
            llm_calls,
        )
        return df.merge(result_df, on="comment_id", how="left")
