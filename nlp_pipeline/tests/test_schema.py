"""Schema validation tests — ensure configs and output contracts are valid."""

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent


class TestConfigSchemas:
    def test_labels_yaml_structure(self):
        with open(ROOT / "labels.yaml") as f:
            data = yaml.safe_load(f)

        assert "labels" in data
        assert "policy" in data
        assert "num_critique_labels" in data
        assert data["num_critique_labels"] == 6

        expected_labels = {
            "STANDARDIZATION",
            "PSEUDO_INDIVIDUALIZATION",
            "COMMODIFICATION_MARKET_LOGIC",
            "REGRESSIVE_LISTENING",
            "AFFECTIVE_PREPACKAGING",
            "FORMAL_RESISTANCE",
            "NONE",
        }
        assert set(data["labels"].keys()) == expected_labels

        for name, label in data["labels"].items():
            assert "id" in label
            assert "description" in label
            assert "short" in label

    def test_regex_rules_yaml_structure(self):
        with open(ROOT / "regex_rules.yaml") as f:
            data = yaml.safe_load(f)

        assert "settings" in data
        assert "rules" in data

        critique_labels = {
            "STANDARDIZATION",
            "PSEUDO_INDIVIDUALIZATION",
            "COMMODIFICATION_MARKET_LOGIC",
            "REGRESSIVE_LISTENING",
            "AFFECTIVE_PREPACKAGING",
            "FORMAL_RESISTANCE",
        }
        assert critique_labels == set(data["rules"].keys())

        for label, rule_set in data["rules"].items():
            assert "patterns" in rule_set, f"{label} missing patterns"
            assert len(rule_set["patterns"]) > 0, f"{label} has no patterns"
            for p in rule_set["patterns"]:
                assert "pattern" in p, f"{label} pattern missing 'pattern' key"
                assert "confidence" in p, f"{label} pattern missing 'confidence'"


class TestOutputContract:
    """Validate that the prediction record contract is correct."""

    def test_prediction_record_schema(self):
        """A valid prediction record should match the contract."""
        record = {
            "comment_id": "abc123",
            "raw_text": "This is a test comment",
            "predicted_labels": ["STANDARDIZATION"],
            "label_probs": {
                "STANDARDIZATION": 0.85,
                "PSEUDO_INDIVIDUALIZATION": 0.12,
                "COMMODIFICATION_MARKET_LOGIC": 0.05,
                "REGRESSIVE_LISTENING": 0.03,
                "AFFECTIVE_PREPACKAGING": 0.08,
                "FORMAL_RESISTANCE": 0.02,
            },
        }

        assert isinstance(record["comment_id"], str)
        assert isinstance(record["predicted_labels"], list)
        assert isinstance(record["label_probs"], dict)

        critique_labels = {
            "STANDARDIZATION",
            "PSEUDO_INDIVIDUALIZATION",
            "COMMODIFICATION_MARKET_LOGIC",
            "REGRESSIVE_LISTENING",
            "AFFECTIVE_PREPACKAGING",
            "FORMAL_RESISTANCE",
        }
        assert critique_labels == set(record["label_probs"].keys())

        for prob in record["label_probs"].values():
            assert 0.0 <= prob <= 1.0

    def test_none_exclusivity(self):
        """NONE should only appear when no critique labels are predicted."""
        assert _is_none_valid(["NONE"], {})
        assert _is_none_valid(["STANDARDIZATION"], {"STANDARDIZATION": 0.8})
        assert not _is_none_valid(
            ["NONE", "STANDARDIZATION"], {"STANDARDIZATION": 0.8}
        )


def _is_none_valid(predicted: list[str], probs: dict) -> bool:
    """Check if NONE label follows the exclusivity policy."""
    has_none = "NONE" in predicted
    has_critique = any(lbl != "NONE" for lbl in predicted)
    if has_none and has_critique:
        return False
    return True
