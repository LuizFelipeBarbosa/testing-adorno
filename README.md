# Testing Adorno

A YouTube comment analysis project that scrapes and analyzes comments from the **Top Tracks of 2025 Global** Spotify playlist. Named after [Theodor W. Adorno](https://en.wikipedia.org/wiki/Theodor_W._Adorno), the influential philosopher and music critic, it applies his Culture Industry critique to modern audience reactions.

## Overview

This project collects YouTube comments from the 15 most popular songs globally in 2025, exploring whether Adorno's theory of passive consumption holds up in modern comment sections. The analysis progresses through three approaches:

1. **Comment length analysis** — Do longer comments contain critique? (Result: mostly catharsis and copypasta)
2. **Engagement analysis** — Do highly-liked/replied comments contain critique? (Result: community building, not critique)
3. **Regex-based NLP classification** — Filter comments for language that maps to Adorno's critique categories

The regex classifier detects six critique labels: STANDARDIZATION, PSEUDO_INDIVIDUALIZATION, COMMODIFICATION_MARKET_LOGIC, REGRESSIVE_LISTENING, AFFECTIVE_PREPACKAGING, and FORMAL_RESISTANCE.

### Featured Artists

Alex Warren · Bad Bunny · HUNTR/X · Taylor Swift · W Sound · Jin · sombr · Olivia Dean · JENNIE · Tate McRae

## Project Structure

```
testing-adorno/
├── testing-adorno.ipynb          # Main analysis notebook
├── adorno_paper_notebook.ipynb   # Paper companion notebook
├── data/
│   ├── comments_merged.json      # ~85K comments (LFS-tracked)
│   └── youtube_urls.csv          # Input: Song Title, Artists, YouTube URL
├── reports/
│   ├── top_comments_by_song.md   # Top 25 longest comments per song
│   ├── top_replies_by_song.md    # Top 25 most-replied comments per song
│   └── matched_comments_detailed.md  # All regex-matched critique comments
├── nlp_pipeline/
│   ├── data_ingest.py            # Data loading & validation
│   ├── preprocess.py             # Text cleaning & feature extraction
│   ├── rule_miner.py             # Regex-based critique classifier
│   ├── utils.py                  # Logging & I/O helpers
│   ├── regex_rules.yaml          # Critique detection patterns
│   ├── labels.yaml               # Label taxonomy
│   ├── tests/                    # Unit tests (111 tests)
│   ├── pipeline_requirements.txt
│   └── Makefile
├── requirements.txt
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.8+
- [Git LFS](https://git-lfs.com/) (required for the JSON dataset)

### Installation

```bash
git clone https://github.com/LuizFelipeBarbosa/testing-adorno.git
cd testing-adorno

git lfs install
git lfs pull

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Usage

Open the main notebook — it contains the full analysis from scraping through NLP classification:

```bash
jupyter notebook testing-adorno.ipynb
```

To run the pipeline tests:

```bash
cd nlp_pipeline
make test
```

## Data

The comment dataset (`data/comments_merged.json`) contains ~85,000 comments with the following fields:

| Field         | Description           |
| ------------- | --------------------- |
| `text`        | Comment text          |
| `song_title`  | Associated song title |
| `artists`     | Artist name(s)        |
| `youtube_url` | Source video URL      |
| `author`      | Comment author        |
| `votes`       | Number of likes       |
| `replies`     | Number of replies     |
| `time`        | Relative timestamp    |

> **Note:** The JSON dataset is tracked with **Git LFS** due to its size.

## Tech Stack

- **Python** — Core scripting language
- **pandas** — Data manipulation
- **youtube-comment-downloader** — Comment scraping
- **Jupyter Notebook** — Interactive analysis
- **matplotlib** — Data visualization
- **pydantic** — Schema validation
- **regex** + **YAML** — Rule-based NLP classification
- **Git LFS** — Large file management

## License

This project is for educational and research purposes.
