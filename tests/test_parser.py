from video_crawler.platforms.bilibili.parser import parse_popular_response, parse_ranking_response


def test_parse_popular_response(bilibili_popular_data):
    videos = parse_popular_response(bilibili_popular_data)
    assert len(videos) == 2

    v = videos[0]
    assert v.platform == "bilibili"
    assert v.video_id == "BV1test000001"
    assert v.title == "测试视频标题一"
    assert v.author_id == "12345"
    assert v.author_name == "测试UP主"
    assert v.view_count == 1_000_000
    assert v.like_count == 50_000
    assert v.coin_count == 20_000
    assert v.duration == 300
    assert v.category == "科技"
    assert "bilibili.com/video/BV1test000001" in v.url


def test_parse_ranking_response(bilibili_ranking_data):
    snapshot = parse_ranking_response(bilibili_ranking_data, "all")
    assert snapshot.platform == "bilibili"
    assert snapshot.category == "all"
    assert len(snapshot.entries) == 2

    first = snapshot.entries[0]
    assert first.rank == 1
    assert first.score == 1_500_000
    assert first.video.video_id == "BV1rank000001"
    assert first.video.view_count == 5_000_000

    second = snapshot.entries[1]
    assert second.rank == 2
    assert second.score == 1_200_000


def test_parse_empty_response():
    data = {"code": 0, "data": {"list": []}}
    videos = parse_popular_response(data)
    assert videos == []
