# 🎵 Testing Adorno

A YouTube comment analysis project that scrapes and analyzes comments from the **Top Tracks of 2025 Global** Spotify playlist. Named after [Theodor W. Adorno](https://en.wikipedia.org/wiki/Theodor_W._Adorno), the influential philosopher and music critic.

## Overview

This project collects YouTube comments from 31 of the most popular songs globally in 2025, enabling sentiment analysis and cultural insight extraction from audience reactions. The pipeline scrapes up to **10,000 comments** distributed evenly across all tracks.

### Featured Artists

Lady Gaga & Bruno Mars · Billie Eilish · ROSÉ · Bad Bunny · Kendrick Lamar & SZA · Sabrina Carpenter · The Weeknd · Chappell Roan · Arctic Monkeys · Coldplay · and more.

## Project Structure

```
testing-adorno/
├── scrape_comments.py          # YouTube comment scraper script
├── testing-adorno.ipynb        # Jupyter notebook for analysis
├── find_youtube_urls.csv       # Input CSV with song metadata & YouTube URLs
├── youtube_comments.json       # Scraped comments dataset (~108 MB, LFS)
├── youtube_comm.json           # Additional comments dataset (~127 MB, LFS)
├── top_comments_by_song.md     # Top comments organized by song
├── Top Tracks of 2025 Global…  # Full playlist reference with YouTube links
├── requirements.txt            # Python dependencies
└── .gitattributes              # Git LFS tracking config
```

## Getting Started

### Prerequisites

- Python 3.8+
- [Git LFS](https://git-lfs.com/) (for large JSON datasets)

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
   ```bash
   pip install -r requirements.txt
   ```

### Usage

**Scrape comments:**
```bash
python scrape_comments.py
```

This will:
- Read YouTube URLs from `find_youtube_urls.csv`
- Scrape up to ~322 comments per video (10,000 total ÷ 31 videos)
- Sort by most popular comments
- Save results to `youtube_comments.json`

**Run the analysis notebook:**
```bash
jupyter notebook testing-adorno.ipynb
```

## Data

The scraped comment data is stored as JSON with the following fields per comment:

| Field         | Description           |
| ------------- | --------------------- |
| `text`        | Comment text          |
| `song_title`  | Associated song title |
| `artists`     | Artist name(s)        |
| `youtube_url` | Source video URL      |

> **Note:** The JSON datasets are tracked with **Git LFS** due to their size (~235 MB combined). Run `git lfs pull` after cloning.

## Tech Stack

- **Python** — Core scripting language
- **pandas** — Data manipulation
- **youtube-comment-downloader** — Comment scraping
- **Jupyter Notebook** — Interactive analysis
- **matplotlib** — Data visualization
- **Git LFS** — Large file storage

## License

This project is for educational and research purposes.
