"""Optional live collection; never overwrites the frozen merged corpus."""

import argparse
import json
from pathlib import Path

import pandas as pd
from youtube_comment_downloader import SORT_BY_POPULAR, YoutubeCommentDownloader

ROOT = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--urls", type=Path, default=ROOT / "data/youtube_urls.csv")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-comments", type=int, default=450_000)
    args = parser.parse_args()
    if args.max_comments < 1:
        parser.error("--max-comments must be positive")
    if args.output.resolve() == (ROOT / "data/comments_merged.json").resolve():
        parser.error("choose a separate output; the frozen corpus is read-only")
    if args.output.exists():
        parser.error("output already exists; choose a new filename")
    if not args.output.parent.is_dir():
        parser.error("output directory must already exist")
    downloader = YoutubeCommentDownloader()
    collected = []
    for _, row in pd.read_csv(args.urls).iterrows():
        if len(collected) >= args.max_comments:
            break
        try:
            for comment in downloader.get_comments_from_url(
                row["YouTube URL"], sort_by=SORT_BY_POPULAR
            ):
                comment.update(
                    song_title=row["Song Title"],
                    artists=row["Artists"],
                    youtube_url=row["YouTube URL"],
                )
                collected.append(comment)
                if len(collected) >= args.max_comments:
                    break
        except Exception as error:
            print(f"Partial collection for {row['Song Title']}: {error}")
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(collected, stream, ensure_ascii=False, indent=2)
    print(
        f"Saved {len(collected):,} comments to {args.output}; completeness is not guaranteed."
    )


if __name__ == "__main__":
    main()
