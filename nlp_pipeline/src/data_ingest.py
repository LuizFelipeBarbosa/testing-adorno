"""Stage 0 -- Data validation and profiling for YouTube comment critique detection.

Responsibilities
----------------
* Accept CSV, JSON, or JSONL input with at minimum ``comment_id`` and ``text``.
* Infer missing optional fields where safe (e.g. hash-based ``comment_id``).
* Validate schema: required fields, types, nulls, duplicates.
* Profile the data: text-length distributions, null counts, duplicate counts,
  language distribution.
* Handle edge cases: empty text, emoji-only, extremely long text, encoding
  issues.
* Return a clean :class:`pandas.DataFrame` ready for downstream stages.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from pydantic import BaseModel, Field, field_validator

from src.utils.logging_utils import get_logger
from src.utils.io_utils import load_jsonl, load_json, project_root, save_json, ensure_dir

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_REQUIRED_FIELDS: list[str] = ["comment_id", "text"]
_OPTIONAL_FIELDS: list[str] = [
    "video_id",
    "like_count",
    "published_at",
    "language",
]
_ALL_FIELDS: list[str] = _REQUIRED_FIELDS + _OPTIONAL_FIELDS

_MAX_TEXT_LENGTH: int = 50_000  # characters; longer comments are truncated

# Common field name aliases from YouTube scraper exports.
_FIELD_ALIASES: dict[str, str] = {
    "cid": "comment_id",
    "votes": "like_count",
    "time_parsed": "published_at",
}
_EMOJI_PATTERN: re.Pattern[str] = re.compile(
    "[\U00010000-\U0010ffff"   # supplementary multilingual plane
    "\U00002700-\U000027BF"    # dingbats
    "\U0000FE00-\U0000FE0F"    # variation selectors
    "\U0000200D"               # zero-width joiner
    "]+",
    flags=re.UNICODE,
)


# ---------------------------------------------------------------------------
# Pydantic schema
# ---------------------------------------------------------------------------

class CommentRecord(BaseModel):
    """Pydantic model for a single YouTube comment record.

    Validates types, coerces values, and applies lightweight cleaning rules.
    """

    comment_id: str = Field(
        ...,
        min_length=1,
        description="Unique identifier for the comment.",
    )
    text: str = Field(
        ...,
        description="Raw comment text.  May be empty after stripping.",
    )
    video_id: Optional[str] = Field(
        default=None,
        description="YouTube video ID the comment belongs to.",
    )
    like_count: Optional[int] = Field(
        default=None,
        ge=0,
        description="Number of likes on the comment.",
    )
    published_at: Optional[str] = Field(
        default=None,
        description="ISO-8601 publication timestamp.",
    )
    language: Optional[str] = Field(
        default=None,
        description="BCP-47 language tag (e.g. 'en', 'de').",
    )

    # -- validators --------------------------------------------------------

    @field_validator("text", mode="before")
    @classmethod
    def coerce_text_to_str(cls, v: Any) -> str:
        """Ensure *text* is always a string, even if the source value is
        numeric or ``None``."""
        if v is None:
            return ""
        return str(v)

    @field_validator("comment_id", mode="before")
    @classmethod
    def coerce_comment_id(cls, v: Any) -> str:
        """Coerce *comment_id* to a non-empty string."""
        if v is None or (isinstance(v, str) and not v.strip()):
            raise ValueError("comment_id must be a non-empty string")
        return str(v).strip()

    @field_validator("like_count", mode="before")
    @classmethod
    def coerce_like_count(cls, v: Any) -> Optional[int]:
        """Coerce *like_count* to ``int | None``.  Accepts stringified ints
        and abbreviated formats like ``"2K"`` or ``"1.5M"``."""
        if v is None or (isinstance(v, str) and not v.strip()):
            return None
        s = str(v).strip().upper().replace(",", "")
        multipliers = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}
        for suffix, mult in multipliers.items():
            if s.endswith(suffix):
                try:
                    val = int(float(s[:-1]) * mult)
                    return max(val, 0)
                except (TypeError, ValueError):
                    return None
        try:
            val = int(float(s))
        except (TypeError, ValueError):
            return None
        return max(val, 0)

    @field_validator("language", mode="before")
    @classmethod
    def normalise_language(cls, v: Any) -> Optional[str]:
        """Lower-case the language tag for consistency."""
        if v is None or (isinstance(v, str) and not v.strip()):
            return None
        return str(v).strip().lower()


# ---------------------------------------------------------------------------
# Format detection
# ---------------------------------------------------------------------------

def detect_format(path: Path) -> str:
    """Auto-detect file format from the file extension.

    Parameters
    ----------
    path:
        Path to the input file.

    Returns
    -------
    str
        One of ``"csv"``, ``"json"``, or ``"jsonl"``.

    Raises
    ------
    ValueError
        If the extension is not recognised.
    """
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return "csv"
    if suffix == ".json":
        return "json"
    if suffix in {".jsonl", ".ndjson"}:
        return "jsonl"
    raise ValueError(
        f"Cannot auto-detect format for extension '{suffix}'. "
        "Pass format='csv', 'json', or 'jsonl' explicitly."
    )


# ---------------------------------------------------------------------------
# Loading helpers
# ---------------------------------------------------------------------------

def _load_csv(path: Path) -> pd.DataFrame:
    """Read a CSV file into a DataFrame, handling common encoding pitfalls."""
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            df = pd.read_csv(path, encoding=encoding, dtype=str)
            logger.info("Loaded CSV with encoding=%s  rows=%d", encoding, len(df))
            return df
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Failed to decode CSV at {path} with any supported encoding.")


def _load_json_file(path: Path) -> pd.DataFrame:
    """Load a JSON file (expected to be a list of objects) into a DataFrame."""
    data = load_json(path)
    if isinstance(data, dict):
        # Some exports wrap the list under a key; try common names.
        for key in ("comments", "items", "data", "results"):
            if key in data and isinstance(data[key], list):
                data = data[key]
                logger.info("Unwrapped JSON under key '%s'.", key)
                break
        else:
            raise ValueError(
                "JSON root is a dict but no known list key was found. "
                "Expected a list of comment objects."
            )
    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON list of objects, got {type(data).__name__}.")
    logger.info("Loaded JSON  rows=%d", len(data))
    return pd.DataFrame(data).astype(str)


def _load_jsonl_file(path: Path) -> pd.DataFrame:
    """Load a JSONL / NDJSON file into a DataFrame."""
    records = load_jsonl(path)
    logger.info("Loaded JSONL  rows=%d", len(records))
    return pd.DataFrame(records).astype(str)


_LOADERS: dict[str, Any] = {
    "csv": _load_csv,
    "json": _load_json_file,
    "jsonl": _load_jsonl_file,
}


# ---------------------------------------------------------------------------
# Schema validation & coercion
# ---------------------------------------------------------------------------

def _generate_comment_id(text: str, index: int) -> str:
    """Generate a deterministic comment_id by hashing the text and row index.

    Parameters
    ----------
    text:
        The comment text.
    index:
        Row index in the DataFrame (used as a salt to avoid collisions for
        duplicate texts).

    Returns
    -------
    str
        A 16-character hex digest.
    """
    payload = f"{text}::{index}".encode("utf-8", errors="replace")
    return hashlib.sha256(payload).hexdigest()[:16]


def _is_emoji_only(text: str) -> bool:
    """Return ``True`` if *text* consists entirely of emoji characters and
    whitespace."""
    stripped = _EMOJI_PATTERN.sub("", text).strip()
    return len(stripped) == 0 and len(text.strip()) > 0


def validate_schema(df: pd.DataFrame) -> pd.DataFrame:
    """Validate, coerce, and clean a raw DataFrame against the comment schema.

    Steps performed:

    1. Ensure required columns exist (infer ``comment_id`` from hash if absent).
    2. Add missing optional columns with ``None``.
    3. Fix encoding artefacts in *text*.
    4. Truncate extremely long texts.
    5. Flag emoji-only and empty-text rows.
    6. Validate every row through :class:`CommentRecord`.
    7. Drop duplicate ``comment_id`` values (keep first).

    Parameters
    ----------
    df:
        Raw DataFrame loaded from disk.

    Returns
    -------
    pd.DataFrame
        Cleaned DataFrame with all columns from :data:`_ALL_FIELDS` plus
        ``_emoji_only`` and ``_empty_text`` boolean flags.
    """
    df = df.copy()

    # ---- 0. apply field aliases ----------------------------------------
    rename_map = {
        src: dst for src, dst in _FIELD_ALIASES.items()
        if src in df.columns and dst not in df.columns
    }
    if rename_map:
        logger.info("Applying field aliases: %s", rename_map)
        df = df.rename(columns=rename_map)

    # ---- 1. required columns -------------------------------------------
    if "text" not in df.columns:
        raise ValueError(
            "Input data must contain a 'text' column.  "
            f"Found columns: {list(df.columns)}"
        )

    if "comment_id" not in df.columns:
        logger.warning(
            "Column 'comment_id' missing -- generating IDs from text hash."
        )
        df["comment_id"] = [
            _generate_comment_id(str(row.get("text", "")), idx)
            for idx, row in df.iterrows()
        ]

    # ---- 2. optional columns -------------------------------------------
    for col in _OPTIONAL_FIELDS:
        if col not in df.columns:
            logger.info("Optional column '%s' not present; filling with None.", col)
            df[col] = None

    # ---- 3. encoding clean-up ------------------------------------------
    df["text"] = (
        df["text"]
        .fillna("")
        .astype(str)
        .str.replace("\x00", "", regex=False)        # null bytes
        .str.replace("\r\n", "\n", regex=False)       # normalise newlines
        .str.replace("\r", "\n", regex=False)
    )

    # ---- 4. truncate extreme lengths -----------------------------------
    long_mask = df["text"].str.len() > _MAX_TEXT_LENGTH
    n_long = long_mask.sum()
    if n_long:
        logger.warning(
            "Truncating %d comments exceeding %d characters.",
            n_long,
            _MAX_TEXT_LENGTH,
        )
        df.loc[long_mask, "text"] = df.loc[long_mask, "text"].str[:_MAX_TEXT_LENGTH]

    # ---- 5. flag edge cases --------------------------------------------
    df["_empty_text"] = df["text"].str.strip().eq("")
    df["_emoji_only"] = df["text"].apply(_is_emoji_only)

    n_empty = df["_empty_text"].sum()
    n_emoji = df["_emoji_only"].sum()
    if n_empty:
        logger.warning("%d rows have empty text after stripping.", n_empty)
    if n_emoji:
        logger.info("%d rows contain emoji-only text.", n_emoji)

    # ---- 6. per-row pydantic validation --------------------------------
    valid_rows: list[dict[str, Any]] = []
    n_invalid = 0
    for idx, row in df.iterrows():
        record_data = {
            col: (row[col] if col in row and pd.notna(row[col]) else None)
            for col in _ALL_FIELDS
        }
        try:
            record = CommentRecord(**record_data)
            validated = record.model_dump()
            # Preserve the boolean flags (not part of pydantic model).
            validated["_empty_text"] = row["_empty_text"]
            validated["_emoji_only"] = row["_emoji_only"]
            valid_rows.append(validated)
        except Exception as exc:  # noqa: BLE001
            n_invalid += 1
            logger.debug("Row %s failed validation: %s", idx, exc)

    if n_invalid:
        logger.warning(
            "Dropped %d / %d rows that failed schema validation.",
            n_invalid,
            len(df),
        )

    result = pd.DataFrame(valid_rows)

    # ---- 7. deduplicate ------------------------------------------------
    n_before = len(result)
    result = result.drop_duplicates(subset="comment_id", keep="first")
    n_dupes = n_before - len(result)
    if n_dupes:
        logger.warning("Removed %d duplicate comment_id entries.", n_dupes)

    result = result.reset_index(drop=True)
    logger.info(
        "Schema validation complete.  %d valid rows retained.", len(result)
    )
    return result


# ---------------------------------------------------------------------------
# Data profiling
# ---------------------------------------------------------------------------

def profile_data(df: pd.DataFrame) -> dict[str, Any]:
    """Generate profiling statistics for a validated comments DataFrame.

    Parameters
    ----------
    df:
        Validated DataFrame (output of :func:`validate_schema`).

    Returns
    -------
    dict
        An EDA summary dictionary with the following top-level keys:

        * ``row_count`` -- total number of rows.
        * ``null_counts`` -- per-column null / NaN counts.
        * ``duplicate_comment_ids`` -- number of duplicate ``comment_id`` values.
        * ``text_length`` -- descriptive statistics for ``text`` length.
        * ``empty_text_count`` -- number of empty-text rows.
        * ``emoji_only_count`` -- number of emoji-only rows.
        * ``language_distribution`` -- value counts for ``language``.
        * ``like_count_stats`` -- descriptive statistics for ``like_count``.
    """
    text_lengths = df["text"].str.len()

    null_counts: dict[str, int] = {}
    for col in _ALL_FIELDS:
        if col in df.columns:
            null_counts[col] = int(df[col].isna().sum())

    dup_ids = int(df["comment_id"].duplicated().sum())

    lang_dist: dict[str, int] = {}
    if "language" in df.columns:
        counts = df["language"].dropna().value_counts()
        lang_dist = {str(k): int(v) for k, v in counts.items()}

    like_stats: dict[str, Any] = {}
    if "like_count" in df.columns:
        numeric_likes = pd.to_numeric(df["like_count"], errors="coerce")
        if numeric_likes.notna().any():
            desc = numeric_likes.describe()
            like_stats = {k: float(v) for k, v in desc.items()}

    profile: dict[str, Any] = {
        "row_count": len(df),
        "null_counts": null_counts,
        "duplicate_comment_ids": dup_ids,
        "text_length": {
            "min": int(text_lengths.min()) if len(df) else 0,
            "max": int(text_lengths.max()) if len(df) else 0,
            "mean": round(float(text_lengths.mean()), 2) if len(df) else 0.0,
            "median": round(float(text_lengths.median()), 2) if len(df) else 0.0,
            "std": round(float(text_lengths.std()), 2) if len(df) else 0.0,
            "p25": round(float(text_lengths.quantile(0.25)), 2) if len(df) else 0.0,
            "p75": round(float(text_lengths.quantile(0.75)), 2) if len(df) else 0.0,
            "p95": round(float(text_lengths.quantile(0.95)), 2) if len(df) else 0.0,
        },
        "empty_text_count": int(df["_empty_text"].sum()) if "_empty_text" in df.columns else 0,
        "emoji_only_count": int(df["_emoji_only"].sum()) if "_emoji_only" in df.columns else 0,
        "language_distribution": lang_dist,
        "like_count_stats": like_stats,
    }

    logger.info(
        "Profiling complete: %d rows, %d nulls in text, %d duplicates.",
        profile["row_count"],
        null_counts.get("text", 0),
        dup_ids,
    )
    return profile


# ---------------------------------------------------------------------------
# Save profiling report
# ---------------------------------------------------------------------------

def save_profile(profile: dict[str, Any], output_dir: str | Path) -> Path:
    """Persist a profiling report to disk as JSON.

    Parameters
    ----------
    profile:
        The dictionary returned by :func:`profile_data`.
    output_dir:
        Directory where the report will be saved.

    Returns
    -------
    Path
        Absolute path to the saved JSON file.
    """
    out = Path(output_dir)
    ensure_dir(out)
    dest = out / "data_profile.json"
    save_json(profile, dest)
    logger.info("Profiling report saved to %s", dest)
    return dest.resolve()


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def ingest(path: str | Path, *, format: str = "auto") -> pd.DataFrame:
    """Load, validate, and profile YouTube comment data.

    This is the single entry point for Stage 0 of the pipeline.

    Parameters
    ----------
    path:
        Path to the input file (CSV, JSON, or JSONL).
    format:
        File format.  ``"auto"`` (default) detects from the file extension.
        Explicit values: ``"csv"``, ``"json"``, ``"jsonl"``.

    Returns
    -------
    pd.DataFrame
        Validated and cleaned DataFrame.  The profiling report is attached as
        the ``attrs["profile"]`` dict on the returned DataFrame, making it
        accessible without a separate call.

    Raises
    ------
    FileNotFoundError
        If *path* does not point to an existing file.
    ValueError
        If the format cannot be determined or the data is fundamentally
        malformed.

    Examples
    --------
    >>> df = ingest("../data/raw/comments.json")
    >>> df.attrs["profile"]["row_count"]
    1523
    """
    path = Path(path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Input file not found: {path}")

    # -- detect format ---------------------------------------------------
    fmt = format if format != "auto" else detect_format(path)
    fmt = fmt.lower()
    logger.info("Ingesting %s  (format=%s)", path.name, fmt)

    loader = _LOADERS.get(fmt)
    if loader is None:
        raise ValueError(
            f"Unsupported format '{fmt}'. Choose from: {list(_LOADERS)}"
        )

    # -- load ------------------------------------------------------------
    raw_df = loader(path)
    if raw_df.empty:
        logger.warning("Input file yielded an empty DataFrame.")
        return raw_df

    # -- validate --------------------------------------------------------
    validated_df = validate_schema(raw_df)

    # -- profile ---------------------------------------------------------
    profile = profile_data(validated_df)
    validated_df.attrs["profile"] = profile

    logger.info(
        "Ingestion complete: %d rows ingested from %s.",
        len(validated_df),
        path.name,
    )
    return validated_df
