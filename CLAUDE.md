# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

YouTube comment analysis project that scrapes and analyzes comments from the **Top Tracks of 2025 Global** Spotify playlist, applying Theodor Adorno's Culture Industry critique. Collects up to 310,000 comments across 31 tracks and generates reports.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
git lfs install && git lfs pull   # required — JSON datasets are LFS-tracked (~235 MB+)
```

Python 3.8+ required. The `.venv/` directory is already present in the repo.

## Key Commands

```bash
# Run the analysis notebook
jupyter notebook testing-adorno.ipynb

# Or run non-interactively
jupyter nbconvert --to notebook --execute testing-adorno.ipynb
```

There are no tests, linters, or build steps in this project.

## Architecture

All logic lives in a single Jupyter notebook (`testing-adorno.ipynb`):

1. **Scraping cell** — Uses `youtube-comment-downloader` to fetch comments from URLs in `find_youtube_urls.csv`, distributes evenly across videos, saves to `youtube_comments.json`
2. **Loading cell** — Reads `youtube_comments.json` into a pandas DataFrame
3. **Visualization cell** — Generates per-song histograms of comment text length using matplotlib
4. **Report cells** — Exports top 25 longest comments and top 25 most-replied comments per song to markdown files

## Data Flow

```
find_youtube_urls.csv → (scrape) → youtube_comments.json → (analyze) → top_comments_by_song.md
                                                                      → top_replies_by_song.md
```

- `find_youtube_urls.csv` — Input: Song Title, Artists, YouTube URL, Video Type columns
- `youtube_comments.json` — Primary dataset with fields: text, song_title, artists, youtube_url, author, votes, time, replies
- `youtube_comments_old.json` / `youtube_comments_merged.json` — Historical/merged comment snapshots
- All JSON files are Git LFS tracked (see `.gitattributes`)

## Critique Detection Pipeline

An 8-stage NLP pipeline (`src/`) classifies YouTube comments into Adorno-grounded critique categories (multi-label: STANDARDIZATION, PSEUDO_INDIVIDUALIZATION, COMMODIFICATION_MARKET_LOGIC, REGRESSIVE_LISTENING, AFFECTIVE_PREPACKAGING, FORMAL_RESISTANCE, NONE).

```bash
pip install -r pipeline_requirements.txt   # separate from scraping deps
make test                                   # 71 unit tests
make pipeline                               # run stages 0-5 end-to-end
python -m src.infer data/raw/comments.jsonl # inference on new data
```

Pipeline stages: data_ingest → preprocess → rule_miner → embed_retrieval → weak_label_llm → train_baseline/train_transformer → infer → evaluate → active_learning. Config in `configs/`, docs in `docs/`, notebooks in `notebooks/`.

## Important Notes

- The scraper cell takes significant time to run (rate-limited with `time.sleep(1)` between videos)
- Comment count target is configurable via `MAX_COMMENTS` in the scraping cell
- The `youtube-comment-downloader` dependency is installed from GitHub master, not PyPI
- Pipeline config files use single-quoted YAML strings for regex patterns (no double quotes with backslash escapes)
