# Testing Adorno

An exploratory analysis of **84,816 stored YouTube comments associated with 15 selected songs released in 2025**. The project asks how listeners discuss standardization, commercial production, listening habits and artistic distinction through an Adorno-inspired vocabulary.

**269 comments match at least one configured rule (0.32%). This is a lexical match rate, not a validated estimate of critical engagement or listener passivity.**

## Read the analysis

- [Notebook](testing-adorno.ipynb): scope, corpus audit, raw/cleaned measurements, rule outputs, examples and nine figures.
- [Essay source](https://github.com/LuizFelipeBarbosa/portfolio-website/blob/main/data/articles/adorno-culture-industry-youtube.js): philosophical interpretation; consult the notebook for computational definitions.
- [Pattern definitions](nlp_pipeline/regex_rules.yaml) and [label taxonomy](nlp_pipeline/labels.yaml): operational vocabulary and intended policies.

## Corpus and selection

The intended selection is the top-streamed **songs first released in 2025**. Songs released in 2024 do not qualify even if they were popular during 2025. This differs from an unfiltered ranking of streams during 2025.

The reproducible song list is [youtube_urls.csv](data/youtube_urls.csv). It contains five solo Bad Bunny entries plus **VeLDÁ**, credited to Bad Bunny, Omar Courtz and Dei V. The original ranking source, stream totals and snapshot date were not retained. The repository therefore documents a fixed selection of 15 songs; it cannot independently establish their precise historical top-15 rank. Spotify's *Top Tracks of 2025 Global* playlist is not itself a release-year filter.

The frozen [comments_merged.json](data/comments_merged.json) has 84,816 distinct comment IDs and **20 source video URLs**, compared with 15 URLs in the current input CSV. Five songs have two URLs in the merged corpus. Sources include a visualizer as well as music videos. Merge history and per-video retrieval logs were not retained.

Collection used `youtube-comment-downloader` with popularity sorting and a global 450,000-comment cap. This is a convenience corpus, not a random sample or proof of complete retrieval. **66,766 rows (78.72%) are replies**. There are **20,084 repeated normalized texts beyond their first occurrence** after ingestion's newline normalization, trimming and lowercasing. Separate IDs remain separate observations; repeated wording alone does not establish bot activity.

## Reproduce without scraping

Use Python **3.11+** for the pinned notebook environment. [Git LFS](https://git-lfs.com/) is needed for the JSON dataset.

```bash
git clone https://github.com/LuizFelipeBarbosa/testing-adorno.git
cd testing-adorno
git lfs install
git lfs pull
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r nlp_pipeline/pipeline_requirements.txt

# Summary, provenance-safe matched-comment reports, figures and source tables
python analysis.py --figures

# Interactive notebook; Run All never contacts YouTube
jupyter notebook testing-adorno.ipynb

# Headless notebook execution from the repository root
jupyter nbconvert --to notebook --execute testing-adorno.ipynb \
  --output-dir reports/generated --ExecutePreprocessor.timeout=1200

# Unit tests, including repeated-text metadata provenance
python -m pytest nlp_pipeline/tests -q
```

The command line accepts `--dataset`, `--output` and `--language-seed` (default **0**). Allow several minutes for preprocessing. Results go to the ignored `reports/generated/` directory:

| Output | Contents |
| --- | --- |
| `summary.json` | Counts, raw/cleaned length definitions, language seed and input SHA-256 hashes |
| `matched_comments.json` | One record per matched comment ID, with source metadata and match spans |
| `matched_comments_detailed.md` | Manual-review report grouped by label; multi-label comments appear in each matching section |
| `figures/` | Nine PNG/SVG figures, combined PDF and supporting CSV tables |

Language detection is now seeded for repeatable assignments. The seeded run assigns 29,271 comments to English, 12,484 to Spanish and 14,723 to unknown. These differ slightly from the original unseeded notebook; **the six rule counts do not change**. A fixed seed does not validate language accuracy, particularly on short text. Package versions can also affect assignments.

## How the pipeline works

1. **Ingest:** schema validation, aliases, newline normalization, comment-ID deduplication and emoji flags.
2. **Preprocess:** Unicode/entity normalization, URL/mention removal, whitespace cleanup, automatic language assignment and cleaned-text features.
3. **Match:** case-insensitive YAML regex patterns and comment-wide negation suppression; multiple labels can match one comment.
4. **Audit/export:** retain each row's author/song metadata and attach video/reply metadata by **comment ID**, never by repeated text.

`raw_text` means text after ingestion, including newline normalization. `clean_text`, `text_length` and `word_count` refer to preprocessed text. The “trivial” flag means fewer than three alphabetic characters, not an assessed lack of meaning.

| Measurement | Ingested raw text | Cleaned text |
| --- | ---: | ---: |
| Median characters | 19 | 18 |
| Below 25 characters | 48,862 | 50,308 |
| Below 50 characters | 65,359 | 66,332 |
| Empty strings | 0 | 224 |

## Rule results and their meaning

| Label | Matching comments |
| --- | ---: |
| Standardization | 81 |
| Pseudo-individualization | 1 |
| Commodification / market logic | 14 |
| Regressive listening | 7 |
| Affective prepackaging | 3 |
| Formal resistance (inverse polarity) | 166 |

There are **272 assignments across 269 comments**, including **three comments with two labels**. Each overlap pairs standardization with market logic, regressive listening or formal resistance. The overlap matrix diagonal counts all matches for each label, including overlaps.

Legacy API fields named `confidence` and `rule_*_conf` contain the **maximum configured pattern weight** among a label's positive matches. They are not calibrated probabilities or measured precision. `labels.yaml` minimum weights, accuracy targets, sarcasm and quoted-voice policies are design intentions; the matcher does not implement or evaluate them. Any configured negation anywhere in a comment suppresses the entire label.

The figures use counts and full-corpus percentages, per-song denominators, cleaned-length quantiles and **matched-phrase comment coverage**. The phrase chart counts a comment once per exact matched phrase. It replaces the older token-frequency charts, which counted repeated word occurrences; the two metrics must not be interchanged.

### Limitations

- English-oriented rules are applied to a multilingual denominator; unmatched critique can be missed.
- Generic praise (“underrated”, “timeless”), irrelevant mentions and incomplete negation can produce matches without the intended meaning.
- No annotated evaluation set establishes precision, recall or calibration. The match rate is neither a validated upper nor lower bound on critical engagement.
- Popularity sorting, replies, repeated text and unequal samples prevent interpreting per-song rates as independent listener estimates.
- The analysis does not measure audio structure, recommendation-system causality or whether a listener is passive. Selected comments illustrate discourse; they do not confirm or refute Adorno at a population level.

An independent annotation rubric covering both matches and nonmatches, multilingual review and agreement measurement would be needed for semantic validation.

## Optional new collection

Live scraping is separated from the frozen-data notebook:

```bash
python collect_comments.py --output data/new_collection.json --max-comments 450000
```

This uses the current 15-row CSV and popularity ordering. It requires `youtube-comment-downloader` from `requirements.txt`, refuses to replace existing files or the frozen corpus, and reports partial failures. A new scrape will differ from the historical merged dataset; merging or replacing that dataset is a separate research decision.

## Repository map

```text
testing-adorno.ipynb      Reader-facing analysis, audits and visualizations
analysis.py             Frozen-data CLI, metrics and ID-safe reports
figures.py              Shared figure generation and CSV exports
collect_comments.py     Optional live collection, separate from reproduction
data/                   Frozen comments and selected song/video list
nlp_pipeline/           Ingestion, preprocessing, YAML rules and unit tests
reports/                Historical exploratory reports and corrected match audit
reports/generated/      Local regenerated outputs (ignored by Git)
```

The longest-comment and most-replied-comment reports are historical exploratory exports. They are examples for reading, not a labeled evaluation dataset. The tracked matched-comment report is regenerated using comment IDs.
