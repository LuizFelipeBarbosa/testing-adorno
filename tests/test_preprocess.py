"""Tests for the preprocessing module."""

import pandas as pd
import pytest

from src.preprocess import (
    normalize_text,
    remove_urls,
    remove_mentions,
    clean_text,
    extract_features,
    is_empty_or_trivial,
    preprocess_dataframe,
    detect_language_safe,
)


class TestNormalizeText:
    def test_html_entities(self):
        assert "rock & roll" in normalize_text("rock &amp; roll")

    def test_unicode_normalization(self):
        # NFKC should normalize ﬁ to fi
        result = normalize_text("ﬁne")
        assert result == "fine"

    def test_none_handling(self):
        assert normalize_text("") == ""


class TestRemoveUrls:
    def test_http_url(self):
        assert remove_urls("check https://example.com out") == "check  out"

    def test_no_url(self):
        assert remove_urls("no links here") == "no links here"

    def test_multiple_urls(self):
        text = "see http://a.com and https://b.com"
        result = remove_urls(text)
        assert "http" not in result


class TestRemoveMentions:
    def test_at_mention(self):
        assert "@user" not in remove_mentions("hey @user check this")

    def test_no_mention(self):
        assert remove_mentions("hello world") == "hello world"


class TestCleanText:
    def test_full_pipeline(self):
        raw = "  @user check https://example.com &amp; listen!!  "
        result = clean_text(raw)
        assert "@user" not in result
        assert "https://" not in result
        assert "&" in result  # decoded from &amp;
        assert result == result.strip()  # no leading/trailing whitespace

    def test_preserves_meaningful_content(self):
        result = clean_text("this song is formulaic garbage")
        assert "formulaic" in result
        assert "garbage" in result

    def test_empty_string(self):
        assert clean_text("") == ""


class TestExtractFeatures:
    def test_basic_features(self):
        feats = extract_features("Hello World!!")
        assert feats["text_length"] == len("Hello World!!")
        assert feats["word_count"] == 2
        assert feats["exclamation_count"] == 2
        assert feats["question_mark_count"] == 0
        assert feats["caps_ratio"] > 0  # 'H' and 'W'

    def test_empty_string(self):
        feats = extract_features("")
        assert feats["text_length"] == 0
        assert feats["word_count"] == 0
        assert feats["caps_ratio"] == 0.0

    def test_punctuation_ratio(self):
        feats = extract_features("!!!")
        assert feats["punctuation_ratio"] == 1.0

    def test_emoji_count(self):
        feats = extract_features("great song! 🔥🔥🔥")
        assert feats["emoji_count"] >= 3


class TestIsEmptyOrTrivial:
    def test_empty(self):
        assert is_empty_or_trivial("")

    def test_whitespace(self):
        assert is_empty_or_trivial("   ")

    def test_emoji_only(self):
        assert is_empty_or_trivial("🔥🔥🔥")

    def test_valid_text(self):
        assert not is_empty_or_trivial("this is a real comment")

    def test_short_but_alpha(self):
        assert not is_empty_or_trivial("yes")

    def test_two_chars(self):
        assert is_empty_or_trivial("ab")


class TestDetectLanguage:
    def test_english(self):
        lang = detect_language_safe("This is a really great song with amazing lyrics")
        assert lang == "en"

    def test_empty(self):
        lang = detect_language_safe("")
        assert lang == "unknown"

    def test_emoji_only(self):
        lang = detect_language_safe("🔥🔥🔥")
        assert isinstance(lang, str)  # should not crash


class TestPreprocessDataframe:
    def test_basic(self):
        df = pd.DataFrame({
            "text": [
                "Great song! https://example.com",
                "This is formulaic garbage @user",
                "",
                None,
            ]
        })
        result = preprocess_dataframe(df)
        assert "clean_text" in result.columns
        assert "raw_text" in result.columns
        assert "text_length" in result.columns
        assert "word_count" in result.columns
        assert "language" in result.columns
        assert len(result) == 4

    def test_preserves_raw_text(self):
        df = pd.DataFrame({"text": ["hello @world https://x.com"]})
        result = preprocess_dataframe(df)
        assert result["raw_text"].iloc[0] == "hello @world https://x.com"
        assert "@world" not in result["clean_text"].iloc[0]
