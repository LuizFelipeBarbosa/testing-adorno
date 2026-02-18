"""Stage 2: Rule-based high-precision critique detection.

Loads regex patterns from a YAML config file (configs/regex_rules.yaml) and
applies them to detect Adornian critique labels in YouTube comments.  Each
label is associated with a set of positive patterns and optional negation
patterns.  When a positive pattern matches but a negation pattern also matches
in the same text, the positive hit is suppressed.

Typical usage
-------------
>>> from src.rule_miner import RuleMiner
>>> miner = RuleMiner()
>>> result = miner.match_text("all these songs sound the same")
>>> result["STANDARDIZATION"].matched
True
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from src.utils.logging_utils import get_logger
from src.utils.io_utils import load_yaml, project_root

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class RuleMatch:
    """Result of applying one label's rule set to a single piece of text.

    Attributes
    ----------
    label : str
        The critique label (e.g. ``"STANDARDIZATION"``).
    matched : bool
        ``True`` if at least one positive pattern matched *and* the match
        was **not** suppressed by a negation pattern.
    confidence : float
        The maximum confidence prior among all matching positive patterns.
        ``0.0`` when nothing matched.
    spans : list[tuple[int, int, str]]
        List of ``(start, end, matched_text)`` for every positive-pattern
        match found in the text.
    negated : bool
        ``True`` when a positive pattern matched but was subsequently
        suppressed by a negation pattern.
    """

    label: str
    matched: bool = False
    confidence: float = 0.0
    spans: list[tuple[int, int, str]] = field(default_factory=list)
    negated: bool = False


# ---------------------------------------------------------------------------
# Compiled-rule container (internal)
# ---------------------------------------------------------------------------

@dataclass
class _CompiledLabel:
    """Internal container for one label's compiled regex patterns."""

    positive: list[tuple[re.Pattern, float]]  # (compiled regex, confidence)
    negation: list[re.Pattern]


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class RuleMiner:
    """Apply regex-based rules to detect critique labels in text.

    Parameters
    ----------
    config_path : str | Path | None
        Path to the YAML config file.  Defaults to
        ``<project_root>/configs/regex_rules.yaml``.
    """

    def __init__(self, config_path: str | Path | None = None) -> None:
        if config_path is None:
            config_path = project_root() / "configs" / "regex_rules.yaml"
        self._config_path = Path(config_path)

        logger.info("Loading rule config from %s", self._config_path)
        raw_config: dict[str, Any] = load_yaml(self._config_path)

        self._settings: dict[str, Any] = raw_config.get("settings", {})
        self._case_insensitive: bool = self._settings.get("case_insensitive", True)
        self._word_boundary: bool = self._settings.get("word_boundary", True)

        raw_rules: dict[str, Any] = raw_config.get("rules", {})
        self._rules: dict[str, _CompiledLabel] = self._compile_rules(raw_rules)

        logger.info(
            "Compiled rules for %d labels: %s",
            len(self._rules),
            ", ".join(sorted(self._rules)),
        )

    # ------------------------------------------------------------------
    # Compilation
    # ------------------------------------------------------------------

    def _compile_pattern(
        self,
        pattern_str: str,
        *,
        boundary: bool = False,
        label: str = "",
    ) -> Optional[re.Pattern]:
        """Compile a single regex string, returning ``None`` on failure.

        If *boundary* is ``True`` **and** the global ``word_boundary``
        setting is enabled, the pattern is wrapped with ``\\b`` anchors.
        """
        if boundary and self._word_boundary:
            pattern_str = rf"\b(?:{pattern_str})\b"

        flags = re.IGNORECASE if self._case_insensitive else 0

        try:
            return re.compile(pattern_str, flags)
        except re.error as exc:
            logger.warning(
                "Skipping invalid regex for label '%s': %r -> %s",
                label,
                pattern_str,
                exc,
            )
            return None

    def _compile_rules(self, raw_rules: dict[str, Any]) -> dict[str, _CompiledLabel]:
        """Compile all raw YAML rules into ready-to-use regex objects.

        Parameters
        ----------
        raw_rules : dict
            The ``rules`` mapping from the YAML config.

        Returns
        -------
        dict[str, _CompiledLabel]
            Mapping from label name to its compiled positive and negation
            patterns.
        """
        compiled: dict[str, _CompiledLabel] = {}

        for label, rule_block in raw_rules.items():
            # --- positive patterns ---
            positive: list[tuple[re.Pattern, float]] = []
            for entry in rule_block.get("patterns", []):
                pat_str: str = entry.get("pattern", "")
                confidence: float = float(entry.get("confidence", 0.5))
                boundary: bool = bool(entry.get("boundary", False))

                compiled_pat = self._compile_pattern(
                    pat_str, boundary=boundary, label=label,
                )
                if compiled_pat is not None:
                    positive.append((compiled_pat, confidence))

            # --- negation patterns ---
            negation: list[re.Pattern] = []
            for neg_str in rule_block.get("negation_patterns", []):
                compiled_neg = self._compile_pattern(
                    neg_str, boundary=False, label=f"{label}/negation",
                )
                if compiled_neg is not None:
                    negation.append(compiled_neg)

            compiled[label] = _CompiledLabel(positive=positive, negation=negation)
            logger.debug(
                "Label '%s': %d positive, %d negation patterns compiled",
                label,
                len(positive),
                len(negation),
            )

        return compiled

    # ------------------------------------------------------------------
    # Single-text matching
    # ------------------------------------------------------------------

    def match_text(self, text: str) -> dict[str, RuleMatch]:
        """Apply all rules to a single piece of text.

        Parameters
        ----------
        text : str
            The comment text to evaluate.

        Returns
        -------
        dict[str, RuleMatch]
            Mapping from each label to its :class:`RuleMatch` result.
        """
        results: dict[str, RuleMatch] = {}

        # Handle empty / None text gracefully.
        if not text:
            for label in self._rules:
                results[label] = RuleMatch(label=label)
            return results

        for label, compiled in self._rules.items():
            spans: list[tuple[int, int, str]] = []
            max_conf: float = 0.0

            # Check positive patterns.
            for pattern, confidence in compiled.positive:
                for m in pattern.finditer(text):
                    spans.append((m.start(), m.end(), m.group()))
                    max_conf = max(max_conf, confidence)

            if not spans:
                # No positive match at all.
                results[label] = RuleMatch(label=label)
                continue

            # Check negation patterns.
            negated = False
            for neg_pattern in compiled.negation:
                if neg_pattern.search(text):
                    negated = True
                    break

            results[label] = RuleMatch(
                label=label,
                matched=not negated,
                confidence=max_conf if not negated else 0.0,
                spans=spans,
                negated=negated,
            )

        return results

    # ------------------------------------------------------------------
    # DataFrame matching
    # ------------------------------------------------------------------

    def match_dataframe(
        self,
        df: pd.DataFrame,
        text_col: str = "clean_text",
    ) -> pd.DataFrame:
        """Apply rules to every row of a DataFrame.

        For each label ``L`` the following columns are added:

        * ``rule_L`` (``bool``) -- whether the rule matched.
        * ``rule_L_conf`` (``float``) -- confidence prior (0.0 if no match).
        * ``rule_L_spans`` (``list``) -- matched spans.

        Parameters
        ----------
        df : pd.DataFrame
            Input DataFrame.  Must contain a column named *text_col*.
        text_col : str
            Name of the column containing the text to match against.

        Returns
        -------
        pd.DataFrame
            A **copy** of *df* with the new rule columns appended.
        """
        df = df.copy()

        if text_col not in df.columns:
            raise KeyError(
                f"Text column '{text_col}' not found in DataFrame. "
                f"Available columns: {list(df.columns)}"
            )

        labels = sorted(self._rules)

        # Pre-allocate result lists for efficiency.
        col_matched: dict[str, list[bool]] = {l: [] for l in labels}
        col_conf: dict[str, list[float]] = {l: [] for l in labels}
        col_spans: dict[str, list[list[tuple[int, int, str]]]] = {l: [] for l in labels}

        n = len(df)
        for idx, text in enumerate(df[text_col]):
            if idx > 0 and idx % 5000 == 0:
                logger.info("RuleMiner: processed %d / %d rows", idx, n)

            text_str = str(text) if pd.notna(text) else ""
            matches = self.match_text(text_str)

            for label in labels:
                rm = matches[label]
                col_matched[label].append(rm.matched)
                col_conf[label].append(rm.confidence)
                col_spans[label].append(rm.spans)

        # Assign new columns.
        for label in labels:
            df[f"rule_{label}"] = col_matched[label]
            df[f"rule_{label}_conf"] = col_conf[label]
            df[f"rule_{label}_spans"] = col_spans[label]

        logger.info(
            "RuleMiner: finished processing %d rows across %d labels",
            n,
            len(labels),
        )
        return df

    # ------------------------------------------------------------------
    # Coverage report
    # ------------------------------------------------------------------

    def coverage_report(self, df: pd.DataFrame) -> dict[str, Any]:
        """Compute coverage statistics after :meth:`match_dataframe`.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame that has already been processed by
            :meth:`match_dataframe` (must contain ``rule_*`` columns).

        Returns
        -------
        dict[str, Any]
            A dictionary with the following structure::

                {
                    "total_rows": int,
                    "any_rule_hit": int,
                    "any_rule_hit_pct": float,
                    "per_label": {
                        "<LABEL>": {
                            "hits": int,
                            "hit_pct": float,
                            "avg_confidence": float,
                        },
                        ...
                    },
                }
        """
        total = len(df)
        if total == 0:
            logger.warning("coverage_report called on an empty DataFrame")
            return {
                "total_rows": 0,
                "any_rule_hit": 0,
                "any_rule_hit_pct": 0.0,
                "per_label": {},
            }

        per_label: dict[str, dict[str, Any]] = {}
        any_hit_mask = pd.Series(False, index=df.index)

        for label in sorted(self._rules):
            col_name = f"rule_{label}"
            if col_name not in df.columns:
                logger.warning(
                    "Column '%s' not found in DataFrame; skipping label '%s' "
                    "in coverage report.  Did you run match_dataframe first?",
                    col_name,
                    label,
                )
                continue

            hit_mask = df[col_name].astype(bool)
            hits = int(hit_mask.sum())
            any_hit_mask = any_hit_mask | hit_mask

            conf_col = f"rule_{label}_conf"
            if conf_col in df.columns and hits > 0:
                avg_conf = float(df.loc[hit_mask, conf_col].mean())
            else:
                avg_conf = 0.0

            per_label[label] = {
                "hits": hits,
                "hit_pct": round(hits / total * 100, 2),
                "avg_confidence": round(avg_conf, 4),
            }

        any_hit = int(any_hit_mask.sum())

        report = {
            "total_rows": total,
            "any_rule_hit": any_hit,
            "any_rule_hit_pct": round(any_hit / total * 100, 2),
            "per_label": per_label,
        }

        # Log a human-readable summary.
        logger.info("--- Rule Coverage Report ---")
        logger.info("Total rows: %d", total)
        logger.info("Any rule hit: %d (%.2f%%)", any_hit, report["any_rule_hit_pct"])
        for label, stats in per_label.items():
            logger.info(
                "  %-35s  hits=%5d (%5.2f%%)  avg_conf=%.4f",
                label,
                stats["hits"],
                stats["hit_pct"],
                stats["avg_confidence"],
            )

        return report
