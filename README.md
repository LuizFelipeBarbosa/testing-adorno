# 🎵 Testing Adorno

A YouTube comment analysis project that scrapes and analyzes comments from the **Top Tracks of 2025 Global** Spotify playlist. Named after [Theodor W. Adorno](https://en.wikipedia.org/wiki/Theodor_W._Adorno), the influential philosopher and music critic, it applies his Culture Industry critique to modern audience reactions.

## Overview

This project collects YouTube comments from 31 of the most popular songs globally in 2025, enabling sentiment analysis and cultural insight extraction. The pipeline scrapes up to **310,000 comments** distributed evenly across all tracks, and includes an 8-stage Natural Language Processing (NLP) pipeline to classify comments into Adorno-grounded critique categories.

### Featured Artists

Lady Gaga & Bruno Mars · Billie Eilish · ROSÉ · Bad Bunny · Kendrick Lamar & SZA · Sabrina Carpenter · The Weeknd · Chappell Roan · Arctic Monkeys · Coldplay · and more.

## Project Structure

```
testing-adorno/
├── scraping_and_analysis/      # Scraping & Notebook Analysis
│   ├── notebooks/              # Interactive experimentation & scraping
│   ├── reports/                # Markdown analysis reports
│   └── requirements.txt        # Dependencies for scraping
├── nlp_pipeline/               # 8-stage NLP Critique Pipeline
│   ├── src/                    # Core pipeline modules
│   ├── configs/                # Pipeline configuration
│   ├── docs/                   # Pipeline documentation
│   ├── models/                 # Saved baseline and transformer models
│   ├── outputs/                # Exported predictions and analytics
│   ├── tests/                  # Unit tests for the pipeline
│   ├── scripts/                # Execution scripts
│   ├── Makefile                # Make commands for the NLP pipeline
│   └── pipeline_requirements.txt # Dependencies for the pipeline
├── data/                       # Raw and processed datasets
├── find_youtube_urls.csv       # Input CSV with song metadata & YouTube URLs
├── youtube_comments_merged.json# Scraped merged comments dataset (~130 MB, LFS)
├── youtube_comments.json       # Additional scraped dataset (~126 MB, LFS)
├── youtube_comments_old.json   # Historical comment snapshot (~107 MB, LFS)
└── .gitattributes              # Git LFS tracking config
```

## Getting Started

### Prerequisites

- Python 3.8+
- [Git LFS](https://git-lfs.com/) (required for the large JSON datasets)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/LuizFelipeBarbosa/testing-adorno.git
   cd testing-adorno
   ```

2. **Pull large files:**
   ```bash
   git lfs install
   git lfs pull
   ```

3. **Install dependencies:**
   There are two levels of dependencies based on what you want to run. 
   ```bash
   # Core scraping & basic analysis
   cd scraping_and_analysis
   pip install -r requirements.txt
   cd ..
   
   # NLP critique pipeline 
   cd nlp_pipeline
   pip install -r pipeline_requirements.txt
   cd ..
   ```

### Usage

**1. Scrape comments & basic analysis:**
Navigate to `scraping_and_analysis` and open `notebooks/testing-adorno.ipynb`. This notebook uses `youtube-comment-downloader` to fetch up to 310,000 comments across the 31 videos listed in `find_youtube_urls.csv`. It also generates histograms of comment length and exports top comments.
```bash
cd scraping_and_analysis/notebooks
jupyter notebook testing-adorno.ipynb
```

**2. Run the NLP Critique Detection Pipeline:**
An 8-stage NLP pipeline evaluates comments across several Adorno-grounded classes (e.g. STANDARDIZATION, PSEUDO_INDIVIDUALIZATION, COMMODIFICATION_MARKET_LOGIC). Navigate to `nlp_pipeline` before running. You can run this end-to-end with:
```bash
cd nlp_pipeline
make test       # Run the test suite
make pipeline   # Run stages 0-5 end-to-end
```
You can also run inference on new data:
```bash
cd nlp_pipeline
python -m src.infer ../data/raw/comments.jsonl
```

## Data

The scraped comment datasets are stored as JSON Lines or JSON arrays with the following fields per comment:

| Field         | Description           |
| ------------- | --------------------- |
| `text`        | Comment text          |
| `song_title`  | Associated song title |
| `artists`     | Artist name(s)        |
| `youtube_url` | Source video URL      |
| `author`      | Comment author        |
| `votes`       | Number of likes/votes |
| `replies`     | Number of replies     |
| `time`        | Timestamp             |

> **Note:** Important JSON datasets like `youtube_comments_merged.json` are tracked with **Git LFS** due to their large size.

## Tech Stack

- **Python** — Core scripting language
- **pandas**, **scikit-learn**, **transformers** — NLP pipeline and data manipulation
- **youtube-comment-downloader** — Scraping logic
- **Jupyter Notebook** — Interactive analysis
- **matplotlib** — Data visualization
- **Git LFS** — Large file management

## License

This project is for educational and research purposes.
