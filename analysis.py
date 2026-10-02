"""Reproduce the frozen-corpus analysis without contacting YouTube."""

import argparse
import hashlib
import json
from html import escape
from pathlib import Path

import pandas as pd
from langdetect import DetectorFactory

from figures import create_figures
from nlp_pipeline.data_ingest import ingest
from nlp_pipeline.preprocess import preprocess_dataframe
from nlp_pipeline.rule_miner import RuleMiner

ROOT = Path(__file__).resolve().parent
LABELS = [
    "STANDARDIZATION",
    "PSEUDO_INDIVIDUALIZATION",
    "COMMODIFICATION_MARKET_LOGIC",
    "REGRESSIVE_LISTENING",
    "AFFECTIVE_PREPACKAGING",
    "FORMAL_RESISTANCE",
]
RULE_COLUMNS = [f"rule_{label}" for label in LABELS]


def build_frame(dataset: Path, language_seed: int = 0) -> pd.DataFrame:
    DetectorFactory.seed = language_seed
    source = pd.read_json(dataset).rename(columns={"cid": "comment_id"})
    frame = RuleMiner().match_dataframe(preprocess_dataframe(ingest(dataset)))
    metadata = source[["comment_id", "youtube_url", "reply"]].drop_duplicates(
        "comment_id", keep="first"
    )
    return frame.merge(metadata, on="comment_id", how="left", validate="one_to_one")


def summarize(frame: pd.DataFrame) -> dict:
    label_matrix = frame[RULE_COLUMNS]
    hits = label_matrix.any(axis=1)
    raw_lengths = frame.raw_text.str.len()
    normalized_text = frame.raw_text.str.strip().str.lower()
    lengths = {}
    for name, series in [("raw", raw_lengths), ("cleaned", frame.text_length)]:
        lengths[name] = {
            "median": float(series.median()),
            "below_25": int((series < 25).sum()),
            "below_50": int((series < 50).sum()),
            "empty": int((series == 0).sum()),
        }
    return {
        "comments": len(frame),
        "songs": int(frame.song_title.nunique()),
        "source_video_urls": int(frame.youtube_url.nunique()),
        "any_label": int(hits.sum()),
        "match_rate_percent": float(hits.mean() * 100),
        "label_assignments": int(label_matrix.sum().sum()),
        "multi_label_comments": int((label_matrix.sum(axis=1) > 1).sum()),
        "formal_resistance_only": int(
            (frame.rule_FORMAL_RESISTANCE & ~label_matrix.iloc[:, :5].any(axis=1)).sum()
        ),
        "other_labels": int(label_matrix.iloc[:, :5].any(axis=1).sum()),
        "per_label": {label: int(frame[f"rule_{label}"].sum()) for label in LABELS},
        "lengths": lengths,
        "mean_cleaned_word_count": float(frame.word_count.mean()),
        "trivial_comments": int(frame.is_trivial.sum()),
        "reply_rows": int(frame.reply.sum()),
        "repeated_normalized_texts": int(normalized_text.duplicated().sum()),
        "language_assignments": {
            str(code): int(count)
            for code, count in frame.language.value_counts().items()
        },
    }


def export_matches(frame: pd.DataFrame, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    matched = frame.loc[frame[RULE_COLUMNS].any(axis=1)]
    matched.to_json(
        output / "matched_comments.json", orient="records", force_ascii=False, indent=2
    )
    lines = [
        "# Matched comments — rule audit",
        "",
        "Weights are assigned pattern weights, not calibrated probabilities.",
        "Metadata follows comment IDs; identical text retains its own author and song.",
        "Raw text here has already passed ingestion's newline normalization.",
        "",
    ]
    for label in LABELS:
        rows = matched.loc[matched[f"rule_{label}"]].sort_values(
            f"rule_{label}_conf", ascending=False, kind="stable"
        )
        lines.extend([f"## {label} ({len(rows)} matches)", ""])
        for _, row in rows.iterrows():
            lines.extend(
                [
                    f"### {escape(str(row.author))} — weight {row[f'rule_{label}_conf']:.2f}",
                    "",
                    f"Comment ID: `{row.comment_id}`",
                    "",
                    f"Song: {escape(str(row.song_title))} — {escape(str(row.artists))}",
                    "",
                    f"Source: {row.youtube_url}",
                    "",
                    f"Likes: {row.like_count} | Replies: {row.replies} | Time: {row.time}",
                    "",
                    *[
                        f"> {escape(line)}".rstrip()
                        for line in row.raw_text.splitlines()
                    ],
                    "",
                ]
            )
    (output / "matched_comments_detailed.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def export_analysis(
    frame: pd.DataFrame, dataset: Path, output: Path, seed: int
) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    summary = summarize(frame)
    summary["language_seed"] = seed
    summary["dataset_sha256"] = hashlib.sha256(dataset.read_bytes()).hexdigest()
    summary["rule_config_sha256"] = hashlib.sha256(
        (ROOT / "nlp_pipeline" / "regex_rules.yaml").read_bytes()
    ).hexdigest()
    (output / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    export_matches(frame, output)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset", type=Path, default=ROOT / "data/comments_merged.json"
    )
    parser.add_argument("--output", type=Path, default=ROOT / "reports/generated")
    parser.add_argument("--language-seed", type=int, default=0)
    parser.add_argument("--figures", action="store_true")
    args = parser.parse_args()
    frame = build_frame(args.dataset, args.language_seed)
    summary = export_analysis(frame, args.dataset, args.output, args.language_seed)
    if args.figures:
        create_figures(frame, args.output / "figures", LABELS)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
