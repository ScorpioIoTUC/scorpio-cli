"""Discord HTTP delivery; keep headers, timeouts and errors unchanged."""

from json import dumps
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class DiscordHttpDelivery:
    def send(self, token: str, channel_id: str, message: str) -> str | None:
        request = Request(
            f"https://discord.com/api/v10/channels/{channel_id}/messages",
            data=dumps({"content": message.strip()}).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=10) as response:
                if response.status not in (200, 201):
                    return "Discord rejected the message."
        except HTTPError as error:
            return f"Discord rejected the message ({error.code})."
        except URLError:
            return "Could not connect to Discord."

        return None
