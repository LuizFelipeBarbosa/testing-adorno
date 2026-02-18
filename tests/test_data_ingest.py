"""Tests for the data ingestion module."""

import json
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from src.data_ingest import ingest, validate_schema, profile_data, detect_format


@pytest.fixture
def sample_csv(tmp_path):
    """Create a sample CSV file."""
    data = pd.DataFrame({
        "comment_id": ["c1", "c2", "c3"],
        "text": [
            "This is a great song!",
            "All songs sound the same these days",
            "🔥🔥🔥",
        ],
        "video_id": ["v1", "v1", "v2"],
        "like_count": [10, 5, 100],
    })
    path = tmp_path / "test.csv"
    data.to_csv(path, index=False)
    return path


@pytest.fixture
def sample_jsonl(tmp_path):
    """Create a sample JSONL file."""
    records = [
        {"comment_id": "c1", "text": "This is great!", "video_id": "v1"},
        {"comment_id": "c2", "text": "Generic garbage", "video_id": "v2"},
    ]
    path = tmp_path / "test.jsonl"
    with open(path, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    return path


@pytest.fixture
def sample_json(tmp_path):
    """Create a sample JSON file."""
    records = [
        {"comment_id": "c1", "text": "Hello world"},
        {"comment_id": "c2", "text": "Another comment"},
    ]
    path = tmp_path / "test.json"
    with open(path, "w") as f:
        json.dump(records, f)
    return path


class TestDetectFormat:
    def test_csv(self, sample_csv):
        assert detect_format(sample_csv) == "csv"

    def test_jsonl(self, sample_jsonl):
        assert detect_format(sample_jsonl) == "jsonl"

    def test_json(self, sample_json):
        assert detect_format(sample_json) == "json"


class TestIngest:
    def test_csv_ingest(self, sample_csv):
        df = ingest(sample_csv)
        assert len(df) == 3
        assert "comment_id" in df.columns
        assert "text" in df.columns

    def test_jsonl_ingest(self, sample_jsonl):
        df = ingest(sample_jsonl)
        assert len(df) == 2
        assert "text" in df.columns

    def test_json_ingest(self, sample_json):
        df = ingest(sample_json)
        assert len(df) == 2


class TestValidateSchema:
    def test_valid_data(self):
        df = pd.DataFrame({
            "comment_id": ["c1", "c2"],
            "text": ["Hello", "World"],
        })
        result = validate_schema(df)
        assert len(result) == 2

    def test_missing_text_column(self):
        df = pd.DataFrame({"comment_id": ["c1"], "content": ["Hello"]})
        with pytest.raises(ValueError, match="text"):
            validate_schema(df)

    def test_generates_comment_id(self):
        df = pd.DataFrame({"text": ["Hello world", "Another one"]})
        result = validate_schema(df)
        assert "comment_id" in result.columns
        assert result["comment_id"].nunique() == 2

    def test_handles_duplicates(self):
        df = pd.DataFrame({
            "comment_id": ["c1", "c1", "c2"],
            "text": ["Hello", "Hello", "World"],
        })
        result = validate_schema(df)
        # Should log warning but not crash
        assert len(result) >= 2


class TestProfileData:
    def test_basic_profile(self):
        df = pd.DataFrame({
            "comment_id": ["c1", "c2", "c3"],
            "text": ["Short", "A longer comment here", ""],
        })
        profile = profile_data(df)
        assert "row_count" in profile
        assert profile["row_count"] == 3
        assert "null_counts" in profile
        assert "text_length" in profile
