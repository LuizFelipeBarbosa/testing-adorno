"""Run only Stage 2 (rule mining) on already-ingested data to avoid re-running 18min preprocessing."""
import sys
import time
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.data_ingest import ingest
from src.preprocess import preprocess_dataframe
from src.rule_miner import RuleMiner
from src.utils.io_utils import ensure_dir, save_json

DATA_PATH = Path("data/raw/comments.json")
OUTPUT_DIR = Path("outputs")
ensure_dir(OUTPUT_DIR)

print("Loading and ingesting data...")
t0 = time.time()
df = ingest(DATA_PATH)
print(f"  Ingested {len(df)} rows in {time.time()-t0:.1f}s")

print("Preprocessing (this takes ~18 min for language detection)...")
t1 = time.time()
df = preprocess_dataframe(df)
print(f"  Preprocessed in {time.time()-t1:.1f}s")
print(f"  Trivial: {df['is_trivial'].sum()} ({df['is_trivial'].mean()*100:.1f}%)")

print("\nRunning Stage 2: Rule Mining...")
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

save_json(report, OUTPUT_DIR / "rule_coverage_report.json")

# Save top matches per label
CRITIQUE_LABELS = [
    "STANDARDIZATION", "PSEUDO_INDIVIDUALIZATION",
    "COMMODIFICATION_MARKET_LOGIC", "REGRESSIVE_LISTENING",
    "AFFECTIVE_PREPACKAGING", "FORMAL_RESISTANCE",
]
samples = {}
print()
print("Sample critique detections:")
for label in CRITIQUE_LABELS:
    rule_col = f"rule_{label}"
    conf_col = f"rule_{label}_conf"
    if rule_col in df.columns:
        matched = df[df[rule_col] == True].sort_values(conf_col, ascending=False)
        if len(matched) > 0:
            print(f"\n  -- {label} ({len(matched)} matches) --")
            for _, row in matched.head(5).iterrows():
                text = row.get("clean_text", row.get("raw_text", ""))[:150]
                print(f"    [{row[conf_col]:.2f}] {text}")
            samples[label] = [
                {"comment_id": r["comment_id"], "text": str(r.get("clean_text", r.get("raw_text", "")))[:300], "confidence": float(r[conf_col])}
                for _, r in matched.head(20).iterrows()
            ]

save_json(samples, OUTPUT_DIR / "sample_critique_matches.json")

# Save processed JSONL
processed_path = OUTPUT_DIR / "stage2_processed.jsonl"
save_cols = ["comment_id", "raw_text", "clean_text", "text_length", "word_count", "language", "is_trivial", "like_count"]
for col in df.columns:
    if col.startswith("rule_"):
        save_cols.append(col)
save_df = df[[c for c in save_cols if c in df.columns]]
save_df.to_json(processed_path, orient="records", lines=True, force_ascii=False)
print(f"\nProcessed data saved → {processed_path} ({len(save_df)} rows)")

elapsed = time.time() - t0
print(f"\nPipeline stages 0-2 complete in {elapsed:.1f}s")
