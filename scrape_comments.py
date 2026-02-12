import pandas as pd
import json
import time
from itertools import islice
from youtube_comment_downloader import YoutubeCommentDownloader, SORT_BY_POPULAR

# Load the CSV
df = pd.read_csv('find_youtube_urls.csv')

# Config
MAX_COMMENTS = 10000
OUTPUT_FILE = 'youtube_comments.json'

downloader = YoutubeCommentDownloader()
all_comments = []

# Calculate how many comments per video (distribute evenly)
urls = df['YouTube URL'].dropna().tolist()
num_videos = len(urls)
comments_per_video = MAX_COMMENTS // num_videos
print(f"Scraping up to {comments_per_video} comments per video across {num_videos} videos...")
print(f"Target total: {MAX_COMMENTS} comments\n")

for idx, row in df.iterrows():
    url = row.get('YouTube URL')
    title = row.get('Song Title', 'Unknown')
    artists = row.get('Artists', 'Unknown')

    if pd.isna(url) or not url.strip():
        print(f"  Skipping row {idx} — no URL")
        continue

    print(f"[{idx + 1}/{len(df)}] {title} — {artists}")
    print(f"  URL: {url}")

    try:
        comments = downloader.get_comments_from_url(url, sort_by=SORT_BY_POPULAR)
        count = 0
        for comment in islice(comments, comments_per_video):
            comment['song_title'] = title
            comment['artists'] = artists
            comment['youtube_url'] = url
            all_comments.append(comment)
            count += 1

        print(f"  ✓ Collected {count} comments")
    except Exception as e:
        print(f"  ✗ Error: {e}")

    # Brief pause to avoid rate limiting
    time.sleep(1)

print(f"\nTotal comments collected: {len(all_comments)}")

# Save to JSON
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(all_comments, f, ensure_ascii=False, indent=2)

print(f"Saved to {OUTPUT_FILE}")
