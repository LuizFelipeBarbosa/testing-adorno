"""Run pipeline stages 0-2 on the YouTube comments dataset."""

import sys
import time
import json
from pathlib import Path

# Ensure src is importable
sys.path.insert(0, str(Path(__file__).parent))

from src.data_ingest import ingest, save_profile
from src.preprocess import preprocess_dataframe
from src.rule_miner import RuleMiner
from src.utils.io_utils import ensure_dir, save_json

DATA_PATH = Path("data/raw/comments.json")
OUTPUT_DIR = Path("outputs")
ensure_dir(OUTPUT_DIR)

# ── Stage 0: Ingest ──────────────────────────────────────────────────────
print("=" * 60)
print("STAGE 0: Data Ingestion + Validation")
print("=" * 60)
t0 = time.time()
df = ingest(DATA_PATH)
profile = df.attrs.get("profile", {})
save_profile(profile, OUTPUT_DIR / "eval")
print(f"  Rows ingested: {len(df)}")
print(f"  Empty text: {profile.get('empty_text_count', '?')}")
print(f"  Emoji-only: {profile.get('emoji_only_count', '?')}")
print(f"  Text length mean: {profile.get('text_length', {}).get('mean', '?')}")
print(f"  Stage 0 done in {time.time() - t0:.1f}s")

# ── Stage 1: Preprocessing ───────────────────────────────────────────────
print()
print("=" * 60)
print("STAGE 1: Text Preprocessing + Feature Extraction")
print("=" * 60)
t1 = time.time()
df = preprocess_dataframe(df)
print(f"  Columns: {list(df.columns)}")
print(f"  Trivial comments: {df['is_trivial'].sum()} ({df['is_trivial'].mean()*100:.1f}%)")
lang_top = df["language"].value_counts().head(5)
print(f"  Top languages: {dict(lang_top)}")
print(f"  Stage 1 done in {time.time() - t1:.1f}s")

# ── Stage 2: Rule Mining ─────────────────────────────────────────────────
print()
print("=" * 60)
print("STAGE 2: Rule-Based Critique Detection")
print("=" * 60)
t2 = time.time()
miner = RuleMiner()
df = miner.match_dataframe(df)
report = miner.coverage_report(df)

print(f"  Total comments: {report['total_rows']}")
print(f"  Any rule match: {report['any_rule_hit']} ({report['any_rule_hit_pct']:.1f}%)")
print()
print("  Per-label hits:")
for label, stats in report["per_label"].items():
    print(f"    {label:40s}  {stats['hits']:6d}  ({stats['hit_pct']:.2f}%)")

# Save results
print()
print("=" * 60)
print("Saving outputs...")
print("=" * 60)

# Save rule report
save_json(report, OUTPUT_DIR / "rule_coverage_report.json")
print(f"  Rule report → {OUTPUT_DIR / 'rule_coverage_report.json'}")

# Save processed data as JSONL (for downstream stages)
processed_path = OUTPUT_DIR / "stage2_processed.jsonl"
# Only save key columns to keep file manageable
save_cols = [
    "comment_id", "raw_text", "clean_text", "text_length", "word_count",
    "language", "is_trivial", "like_count",
]
# Add rule columns
for col in df.columns:
    if col.startswith("rule_"):
        save_cols.append(col)

save_df = df[[c for c in save_cols if c in df.columns]]
save_df.to_json(processed_path, orient="records", lines=True, force_ascii=False)
print(f"  Processed data → {processed_path} ({len(save_df)} rows)")

# Save top critique matches per label for review
print()
print("=" * 60)
print("Sample critique detections:")
print("=" * 60)

CRITIQUE_LABELS = [
    "STANDARDIZATION", "PSEUDO_INDIVIDUALIZATION",
    "COMMODIFICATION_MARKET_LOGIC", "REGRESSIVE_LISTENING",
    "AFFECTIVE_PREPACKAGING", "FORMAL_RESISTANCE",
]
samples = {}
for label in CRITIQUE_LABELS:
    rule_col = f"rule_{label}"
    conf_col = f"rule_{label}_conf"
    if rule_col in df.columns:
        matched = df[df[rule_col] == True].sort_values(conf_col, ascending=False)
        if len(matched) > 0:
            top = matched.head(5)
            print(f"\n  ── {label} ({len(matched)} matches) ──")
            for _, row in top.iterrows():
                text = row["clean_text"][:120] if "clean_text" in row else row["text"][:120]
                print(f"    [{row[conf_col]:.2f}] {text}")
            samples[label] = [
                {"comment_id": r["comment_id"], "text": r.get("clean_text", r.get("raw_text", ""))[:300], "confidence": float(r[conf_col])}
                for _, r in matched.head(20).iterrows()
            ]

save_json(samples, OUTPUT_DIR / "sample_critique_matches.json")
print(f"\n  Samples saved → {OUTPUT_DIR / 'sample_critique_matches.json'}")

elapsed = time.time() - t0
print(f"\n{'=' * 60}")
print(f"Pipeline stages 0-2 complete in {elapsed:.1f}s")
print(f"{'=' * 60}")
