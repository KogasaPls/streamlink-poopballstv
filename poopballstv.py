"""poopballs.tv streamlink plugin.

Requires stream/VOD URL.
"""

import logging
import re

from streamlink.plugin import Plugin
from streamlink.plugin import pluginmatcher
from streamlink.plugin.api import useragents
from streamlink.plugin.api import validate
from streamlink.stream.hls import HLSStream

log = logging.getLogger(__name__)


@pluginmatcher(re.compile(r"https://poopballs\.tv/videos/(?P<id>[^/]+)"))
class PoopBalls(Plugin):
    _BASE_URL = "https://poopballs.tv"
    _VIDEO_URL = "https://poopballs.tv/videos/{id}"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = self.match.group("id")
        self.session.http.headers.update(
            {
                "Origin": self._BASE_URL,
                "Referer": self._VIDEO_URL.format(id=self.id),
                "User-Agent": useragents.CHROME,
            }
        )

    def _get_streams(self):
        video_id = self.id

        api_url = (
            f"https://poopballs.tv/api/v1/vod/{video_id}"
            "?with_channel=true&with_chapters=true&with_muted_segments=true"
        )

        data = self.session.http.get(
            api_url,
            schema=validate.Schema(
                validate.parse_json(),
                validate.any(
                    {
                        "success": True,
                        "data": {
                            "video_path": str,
                            "title": str,
                            "edges": {
                                "channel": {
                                    "display_name": str,
                                },
                            },
                        },
                    },
                ),
                validate.get("data"),
            ),
        )

        if not data:
            return None

        self.title = data.get("title")
        self.author = data.get("edges").get("channel").get("display_name")

        log.info(f"Found video: {self.title} by {self.author}")

        video_path = data.get("video_path")
        if not video_path:
            return None

        log.debug(f"Found video path: {video_path}")
        playlist_url = f"{self._BASE_URL}{video_path}"

        stream = HLSStream(self.session, playlist_url)
        playlist = {"vod": stream}

        return playlist


__plugin__ = PoopBalls
