"""Stage 1: Text preprocessing for YouTube comment critique detection.

This module provides utilities to clean, normalize, and extract features from
raw YouTube comment text.  It is designed as the first stage in an NLP pipeline
that ultimately classifies whether a comment contains meaningful musical
critique.

Key design choices
------------------
* **Preserve voice** -- We deliberately avoid aggressive lowercasing or slang
  removal so that downstream models can leverage the commenter's authentic
  register (e.g. ALL-CAPS emphasis, slang like "fire", "mid", "slaps").
* **Dual-text columns** -- Every row retains both ``raw_text`` (verbatim from
  YouTube) and ``clean_text`` (after normalization) so that either can be used
  depending on the task.
* **Graceful failure** -- Language detection and emoji counting are wrapped in
  safe helpers that never raise; they log warnings and fall back to sensible
  defaults.
"""

from __future__ import annotations

import html
import re
import unicodedata
from typing import Optional

import emoji
import pandas as pd

from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Regex patterns (compiled once at module level for performance)
# ---------------------------------------------------------------------------
_URL_RE = re.compile(
    r"https?://\S+|www\.\S+",
    re.IGNORECASE,
)
_MENTION_RE = re.compile(r"@[\w.]+")
_WHITESPACE_RE = re.compile(r"\s+")


# ---- low-level text helpers ------------------------------------------------

def normalize_text(text: str) -> str:
    """Apply NFKC unicode normalization and decode HTML entities.

    Parameters
    ----------
    text : str
        Raw input string.

    Returns
    -------
    str
        Normalized string with HTML entities decoded (e.g. ``&amp;`` becomes
        ``&``).  Two passes of ``html.unescape`` are used because YouTube
        sometimes double-encodes entities (``&amp;amp;``).
    """
    text = unicodedata.normalize("NFKC", text)
    # Double-unescape to handle double-encoded HTML entities from YouTube.
    text = html.unescape(html.unescape(text))
    return text


def remove_urls(text: str) -> str:
    """Strip HTTP(S) and www URLs from *text*.

    Parameters
    ----------
    text : str
        Input string potentially containing URLs.

    Returns
    -------
    str
        String with all URLs removed.
    """
    return _URL_RE.sub("", text)


def remove_mentions(text: str) -> str:
    """Strip ``@mentions`` from *text*.

    Parameters
    ----------
    text : str
        Input string potentially containing ``@user`` mentions.

    Returns
    -------
    str
        String with all mentions removed.
    """
    return _MENTION_RE.sub("", text)


def clean_text(text: str) -> str:
    """Full cleaning pipeline: normalize, remove URLs & mentions, collapse whitespace.

    The cleaning steps are intentionally minimal to preserve the commenter's
    voice -- we do **not** lowercase, stem, or remove slang.

    Parameters
    ----------
    text : str
        Raw comment text.

    Returns
    -------
    str
        Cleaned text ready for feature extraction or downstream modelling.
    """
    text = normalize_text(text)
    text = remove_urls(text)
    text = remove_mentions(text)
    # Collapse runs of whitespace (including newlines) into a single space.
    text = _WHITESPACE_RE.sub(" ", text)
    return text.strip()


# ---- feature extraction ----------------------------------------------------

def extract_features(text: str) -> dict:
    """Compute lightweight text-level features from *text*.

    Features
    --------
    text_length : int
        Number of characters in the string.
    word_count : int
        Number of whitespace-delimited tokens.
    punctuation_ratio : float
        Fraction of characters that are ASCII punctuation.
    caps_ratio : float
        Fraction of alphabetic characters that are uppercase.
    emoji_count : int
        Number of emoji characters (via the ``emoji`` library).
    exclamation_count : int
        Number of ``!`` characters.
    question_mark_count : int
        Number of ``?`` characters.

    Parameters
    ----------
    text : str
        Input string (typically the *cleaned* text, but works on raw text too).

    Returns
    -------
    dict
        Mapping of feature name to computed value.
    """
    length = len(text)
    words = text.split()
    word_count = len(words)

    # Punctuation ratio
    if length > 0:
        punct_count = sum(1 for ch in text if unicodedata.category(ch).startswith("P"))
        punctuation_ratio = punct_count / length
    else:
        punctuation_ratio = 0.0

    # Caps ratio (relative to alphabetic characters only)
    alpha_chars = [ch for ch in text if ch.isalpha()]
    if alpha_chars:
        caps_ratio = sum(1 for ch in alpha_chars if ch.isupper()) / len(alpha_chars)
    else:
        caps_ratio = 0.0

    # Emoji count
    try:
        emoji_count = emoji.emoji_count(text)
    except Exception:  # pragma: no cover -- defensive against emoji lib changes
        logger.warning("emoji.emoji_count failed; falling back to 0")
        emoji_count = 0

    return {
        "text_length": length,
        "word_count": word_count,
        "punctuation_ratio": round(punctuation_ratio, 4),
        "caps_ratio": round(caps_ratio, 4),
        "emoji_count": emoji_count,
        "exclamation_count": text.count("!"),
        "question_mark_count": text.count("?"),
    }


# ---- language detection ----------------------------------------------------

def detect_language_safe(text: str) -> str:
    """Detect the language of *text* with a safe fallback.

    Uses ``langdetect`` under the hood.  If detection fails (e.g. the text is
    too short, emoji-only, or the library is not installed), returns
    ``"unknown"`` instead of raising.

    Parameters
    ----------
    text : str
        Input string.

    Returns
    -------
    str
        ISO 639-1 language code (e.g. ``"en"``, ``"es"``) or ``"unknown"``.
    """
    if not text or not text.strip():
        return "unknown"

    try:
        from langdetect import detect, LangDetectException

        # langdetect needs at least some alphabetic content to work.
        alpha_content = "".join(ch for ch in text if ch.isalpha())
        if len(alpha_content) < 3:
            return "unknown"

        return detect(text)
    except Exception:
        logger.debug("Language detection failed for text: %.60s...", text)
        return "unknown"


# ---- trivial / empty check -------------------------------------------------

def is_empty_or_trivial(text: str, min_alpha_chars: int = 3) -> bool:
    """Check whether *text* is empty, whitespace-only, or trivially short.

    A comment is considered *trivial* if it contains fewer than
    *min_alpha_chars* alphabetic characters.  This catches cases like
    emoji-only comments or strings of punctuation that carry no linguistic
    signal.

    Parameters
    ----------
    text : str
        Input string (may be ``None``).
    min_alpha_chars : int, optional
        Minimum number of alphabetic characters required for a comment to be
        considered non-trivial.  Defaults to ``3``.

    Returns
    -------
    bool
        ``True`` if the text is empty, whitespace-only, or trivially short.
    """
    if text is None:
        return True
    if not isinstance(text, str):
        return True
    if not text.strip():
        return True
    alpha_count = sum(1 for ch in text if ch.isalpha())
    return alpha_count < min_alpha_chars


# ---- DataFrame entry point -------------------------------------------------

def preprocess_dataframe(
    df: pd.DataFrame,
    text_col: str = "text",
) -> pd.DataFrame:
    """Apply the full preprocessing pipeline to a DataFrame of comments.

    This is the main entry point for Stage 1.  It performs the following steps
    for every row:

    1. Copy the original text into ``raw_text``.
    2. Clean the text (normalize, strip URLs/mentions, collapse whitespace)
       and store the result in ``clean_text``.
    3. Detect the language of the cleaned text.
    4. Extract text features and add them as individual columns.

    Rows where the source column is ``NaN`` / ``None`` are handled gracefully:
    ``clean_text`` is set to an empty string and features receive safe
    defaults.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.  Must contain a column named *text_col*.
    text_col : str, optional
        Name of the column that holds the raw comment text.  Defaults to
        ``"text"``.

    Returns
    -------
    pd.DataFrame
        A **copy** of the input DataFrame with the following columns added:

        - ``raw_text`` -- verbatim original text.
        - ``clean_text`` -- preprocessed text.
        - ``language`` -- detected language code.
        - ``is_trivial`` -- boolean flag for empty / emoji-only comments.
        - ``text_length``, ``word_count``, ``punctuation_ratio``,
          ``caps_ratio``, ``emoji_count``, ``exclamation_count``,
          ``question_mark_count`` -- numeric features.

    Raises
    ------
    KeyError
        If *text_col* is not present in *df*.
    """
    if text_col not in df.columns:
        raise KeyError(
            f"Column '{text_col}' not found in DataFrame. "
            f"Available columns: {list(df.columns)}"
        )

    logger.info(
        "Starting preprocessing on %d rows (text_col=%r)", len(df), text_col
    )

    out = df.copy()

    # 1. Preserve raw text ------------------------------------------------
    out["raw_text"] = out[text_col].copy()

    # 2. Clean text -------------------------------------------------------
    def _safe_clean(val: Optional[str]) -> str:
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return ""
        if not isinstance(val, str):
            return str(val)
        return clean_text(val)

    out["clean_text"] = out[text_col].apply(_safe_clean)

    # 3. Detect language --------------------------------------------------
    out["language"] = out["clean_text"].apply(detect_language_safe)

    # 4. Trivial flag -----------------------------------------------------
    out["is_trivial"] = out["clean_text"].apply(is_empty_or_trivial)

    # 5. Extract features -------------------------------------------------
    features_series = out["clean_text"].apply(extract_features)
    features_df = pd.DataFrame(features_series.tolist(), index=out.index)
    out = pd.concat([out, features_df], axis=1)

    # Summary logging
    n_trivial = out["is_trivial"].sum()
    lang_counts = out["language"].value_counts().head(5).to_dict()
    logger.info(
        "Preprocessing complete. %d trivial rows flagged. "
        "Top languages: %s",
        n_trivial,
        lang_counts,
    )

    return out
