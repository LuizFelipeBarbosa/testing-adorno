"""Export rule-based critique label matches to a styled Markdown file.

Replicates the logic in notebooks/02_rule_coverage.ipynb and writes:
    outputs/critique_matched_comments.md

Each critique concept (STANDARDIZATION, PSEUDO_INDIVIDUALIZATION, etc.)
gets its own section.  Within each section every matched comment is
rendered with full text, confidence score, author, votes, and timestamp
— styled like top_replies_by_song.md.
"""

import sys
sys.path.insert(0, '.')

import json
import pandas as pd
from src.data_ingest import ingest
from src.preprocess import preprocess_dataframe
from src.rule_miner import RuleMiner

# ── Configuration ────────────────────────────────────────────────────────
DATA_PATH   = 'youtube_comments_merged.json'
OUTPUT_PATH = 'outputs/critique_matched_comments.md'

CRITIQUE_LABELS = [
    'STANDARDIZATION',
    'PSEUDO_INDIVIDUALIZATION',
    'COMMODIFICATION_MARKET_LOGIC',
    'REGRESSIVE_LISTENING',
    'AFFECTIVE_PREPACKAGING',
    'FORMAL_RESISTANCE',
]

# Human-readable names for each label
LABEL_DISPLAY = {
    'STANDARDIZATION':              'Standardization',
    'PSEUDO_INDIVIDUALIZATION':      'Pseudo-Individualization',
    'COMMODIFICATION_MARKET_LOGIC':  'Commodification / Market Logic',
    'REGRESSIVE_LISTENING':          'Regressive Listening',
    'AFFECTIVE_PREPACKAGING':        'Affective Pre-Packaging',
    'FORMAL_RESISTANCE':             'Formal Resistance',
}

# ── Load raw data to preserve metadata ───────────────────────────────────
print("Loading raw JSON for metadata …")
with open(DATA_PATH, 'r', encoding='utf-8') as fh:
    raw_data = json.load(fh)

# Build a lookup: comment_id (cid) → row metadata
raw_lookup = {}
for item in raw_data:
    cid = item.get('cid', '')
    raw_lookup[cid] = item

# ── Pipeline ─────────────────────────────────────────────────────────────
print("Loading and preprocessing data …")
df = ingest(DATA_PATH)
df = preprocess_dataframe(df)
print(f"Preprocessed {len(df)} comments")

print("Applying rule-based matcher …")
miner = RuleMiner()
df = miner.match_dataframe(df)
report = miner.coverage_report(df)

print(f"Total comments: {report['total_rows']}")
print(f"Any rule hit:   {report['any_rule_hit']} ({report['any_rule_hit_pct']:.1f}%)")
print()

# ── Build Markdown ───────────────────────────────────────────────────────
with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    f.write('# Critique-Label Matched Comments\n\n')
    f.write(f'**Total comments analysed:** {report["total_rows"]}\n\n')
    f.write(f'**Comments matching at least one rule:** '
            f'{report["any_rule_hit"]} ({report["any_rule_hit_pct"]:.1f}%)\n\n')
    f.write('---\n\n')

    for lbl in CRITIQUE_LABELS:
        matched = df[df[f'rule_{lbl}'] == True].copy()
        if len(matched) == 0:
            continue

        # Sort by confidence descending
        matched = matched.sort_values(f'rule_{lbl}_conf', ascending=False)

        display_name = LABEL_DISPLAY.get(lbl, lbl)
        stats = report['per_label'].get(lbl, {})
        hits  = stats.get('hits', len(matched))
        avg_conf = stats.get('avg_confidence', 0.0)

        f.write(f'## 📌 {display_name}\n')
        f.write(f'**Hits:** {hits} · '
                f'**Avg confidence:** {avg_conf:.2f}\n\n')

        for i, (_, row) in enumerate(matched.iterrows(), 1):
            conf = row[f'rule_{lbl}_conf']
            cid  = row.get('comment_id', '')

            # Pull metadata from the raw lookup
            raw = raw_lookup.get(cid, {})
            comment_text = raw.get('text', str(row.get('text', row.get('clean_text', ''))))
            author       = raw.get('author', 'Unknown')
            votes        = raw.get('votes', str(row.get('like_count', '')))
            time_str     = raw.get('time', '')
            song         = raw.get('song_title', '')
            artists      = raw.get('artists', '')

            f.write(f'### {i}. {author} (confidence {conf:.2f})\n\n')
            if song:
                f.write(f'🎵 **Song:** {song}')
                if artists:
                    f.write(f' — {artists}')
                f.write('\n\n')
            f.write(f'> {comment_text}\n\n')
            f.write(f'👍 {votes} · {time_str}\n\n')
            f.write('---\n\n')

    print(f'\nSaved to {OUTPUT_PATH}')
