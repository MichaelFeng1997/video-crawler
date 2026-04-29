import json
from pathlib import Path

from video_crawler.platforms.youtube.parser import (
    parse_duration,
    parse_popular_response,
    parse_ranking_response,
    parse_video,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_fixture():
    return json.loads((FIXTURES_DIR / "youtube_popular.json").read_text())


def test_parse_duration():
    assert parse_duration("PT3M33S") == 213
    assert parse_duration("PT1H2M3S") == 3723
    assert parse_duration("PT45S") == 45
    assert parse_duration("PT10M") == 600
    assert parse_duration("") == 0
    assert parse_duration("invalid") == 0


def test_parse_video():
    data = _load_fixture()
    v = parse_video(data["items"][0])
    assert v.platform == "youtube"
    assert v.video_id == "dQw4w9WgXcQ"
    assert v.title == "Rick Astley - Never Gonna Give You Up"
    assert v.author_id == "UCuAXFkgsw1L7xaCfnd5JJOw"
    assert v.author_name == "Rick Astley"
    assert v.view_count == 1_500_000_000
    assert v.like_count == 16_000_000
    assert v.reply_count == 3_000_000
    assert v.duration == 213
    assert v.coin_count == 0
    assert v.danmaku_count == 0
    assert "youtube.com/watch?v=dQw4w9WgXcQ" in v.url
    assert "rick astley" in v.tags
    assert v.category == "music"


def test_parse_popular_response():
    data = _load_fixture()
    videos = parse_popular_response(data)
    assert len(videos) == 2
    assert videos[0].video_id == "dQw4w9WgXcQ"
    assert videos[1].video_id == "9bZkp7q19f0"


def test_parse_ranking_response():
    data = _load_fixture()
    snapshot = parse_ranking_response(data, "music")
    assert snapshot.platform == "youtube"
    assert snapshot.category == "music"
    assert len(snapshot.entries) == 2
    assert snapshot.entries[0].rank == 1
    assert snapshot.entries[0].score == 1_500_000_000
    assert snapshot.entries[1].rank == 2


def test_parse_empty_response():
    videos = parse_popular_response({"items": []})
    assert videos == []
