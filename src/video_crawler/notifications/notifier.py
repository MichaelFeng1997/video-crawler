from __future__ import annotations

import logging

import apprise

from video_crawler.config import settings

logger = logging.getLogger(__name__)

_apprise_instance: apprise.Apprise | None = None

_TYPE_MAP = {
    "info": apprise.NotifyType.INFO,
    "success": apprise.NotifyType.SUCCESS,
    "failure": apprise.NotifyType.FAILURE,
    "warning": apprise.NotifyType.WARNING,
}


def _get_apprise() -> apprise.Apprise | None:
    global _apprise_instance
    if _apprise_instance is not None:
        return _apprise_instance
    urls = settings.notify_url_list
    if not urls:
        return None
    _apprise_instance = apprise.Apprise()
    for url in urls:
        _apprise_instance.add(url)
    return _apprise_instance


def reset():
    global _apprise_instance
    _apprise_instance = None


def send_notification(title: str, body: str, notify_type: str = "info") -> bool:
    ap = _get_apprise()
    if ap is None:
        logger.debug("No notify URLs configured, skipping notification")
        return False
    try:
        return ap.notify(
            title=title,
            body=body,
            notify_type=_TYPE_MAP.get(notify_type, apprise.NotifyType.INFO),
        )
    except Exception:
        logger.exception("Failed to send notification")
        return False
