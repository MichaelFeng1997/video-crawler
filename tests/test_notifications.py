from unittest.mock import MagicMock, patch

from video_crawler.notifications import notifier


def setup_function():
    notifier.reset()


def test_send_no_urls_configured():
    with patch.object(notifier, "settings") as mock_settings:
        mock_settings.notify_url_list = []
        result = notifier.send_notification("title", "body")
    assert result is False


def test_send_success():
    mock_ap = MagicMock()
    mock_ap.notify.return_value = True
    with patch.object(notifier, "_get_apprise", return_value=mock_ap):
        result = notifier.send_notification("采集完成", "成功采集 100 个视频", "success")
    assert result is True
    mock_ap.notify.assert_called_once()


def test_send_exception_returns_false():
    mock_ap = MagicMock()
    mock_ap.notify.side_effect = RuntimeError("network error")
    with patch.object(notifier, "_get_apprise", return_value=mock_ap):
        result = notifier.send_notification("title", "body")
    assert result is False
