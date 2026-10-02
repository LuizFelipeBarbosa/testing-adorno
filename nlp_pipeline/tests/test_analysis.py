"""Provenance regression: repeated wording must not merge different comments."""

import json

from analysis import build_frame, export_matches


def test_repeated_text_retains_comment_metadata(tmp_path):
    records = [
        {
            "cid": "first",
            "text": "this song is generic",
            "song_title": "Song A",
            "artists": "Artist A",
            "author": "Author A",
            "youtube_url": "https://www.youtube.com/watch?v=first",
            "reply": False,
        },
        {
            "cid": "second",
            "text": "this song is generic",
            "song_title": "Song B",
            "artists": "Artist B",
            "author": "Author B",
            "youtube_url": "https://www.youtube.com/watch?v=second",
            "reply": True,
        },
    ]
    dataset = tmp_path / "comments.json"
    dataset.write_text(json.dumps(records), encoding="utf-8")
    frame = build_frame(dataset)
    export_matches(frame, tmp_path / "output")
    exported = json.loads((tmp_path / "output/matched_comments.json").read_text())
    assert [
        (row["comment_id"], row["author"], row["song_title"], row["youtube_url"])
        for row in exported
    ] == [
        ("first", "Author A", "Song A", records[0]["youtube_url"]),
        ("second", "Author B", "Song B", records[1]["youtube_url"]),
    ]
    assert frame.rule_STANDARDIZATION.all()
