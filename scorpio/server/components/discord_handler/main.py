from typing import Any
from json import dumps
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..storage_handler import StorageHandler


class DiscordHandler:
    """Persist and expose the Discord bot configuration."""

    def __init__(self, storage_handler: StorageHandler) -> None:
        self.storage_handler = storage_handler

    def get_settings(self) -> dict[str, Any]:
        """Return Discord settings without exposing the bot token."""
        discord = self.storage_handler.get().get("discord", {})
        return {
            "configured": bool(discord.get("auth_token")),
            "channels": discord.get("channels", {}),
            "error_alert_gap_minutes": discord.get("error_alert_gap_minutes", 5),
        }

    def setup(self, token: str | None) -> tuple[dict, int]:
        """Create or replace the bot authentication token."""
        if not token or not token.strip():
            return {"error": "Discord token is required."}, 400

        storage = self.storage_handler.get()
        discord = storage.setdefault("discord", {})
        discord["auth_token"] = token.strip()
        discord.setdefault("channels", {})
        discord.setdefault("error_alert_gap_minutes", 5)
        self.storage_handler.update(storage)
        return {"message": "Discord token updated.", "configured": True}, 200

    def set_channel(self, tag: str | None, channel_id: str | None) -> tuple[dict, int]:
        """Create or update a channel mapping by tag."""
        if not tag or not tag.strip() or not channel_id or not channel_id.strip():
            return {"error": "Tag and channel_id are required."}, 400

        storage = self.storage_handler.get()
        discord = storage.setdefault("discord", {})
        channels = discord.setdefault("channels", {})
        channels[tag.strip()] = channel_id.strip()
        self.storage_handler.update(storage)
        return {"message": "Discord channel updated.", "channels": channels}, 200

    def set_alert_gap(self, minutes: Any) -> tuple[dict, int]:
        """Set the minimum interval between error alerts."""
        try:
            gap = int(minutes)
            if gap < 1:
                raise ValueError
        except (TypeError, ValueError):
            return {"error": "minutes must be a positive integer."}, 400

        storage = self.storage_handler.get()
        discord = storage.setdefault("discord", {})
        discord["error_alert_gap_minutes"] = gap
        self.storage_handler.update(storage)
        return {"message": "Discord alert interval updated.", "minutes": gap}, 200

    def remove(self) -> tuple[dict, int]:
        """Remove every Discord setting from the storage."""
        storage = self.storage_handler.get()
        storage.pop("discord", None)
        self.storage_handler.update(storage)
        return {"message": "Discord configuration removed.", "configured": False}, 200

    def notify(self, message: str | None, tag: str | None) -> tuple[dict, int]:
        """Send a message to the Discord channel mapped by tag."""
        if not message or not message.strip() or not tag or not tag.strip():
            return {"error": "Message and tag are required."}, 400

        discord = self.storage_handler.get().get("discord", {})
        token = discord.get("auth_token")
        channel_id = discord.get("channels", {}).get(tag.strip())
        if not token:
            return {"error": "Discord bot is not configured."}, 400
        if not channel_id:
            return {"error": f"No Discord channel configured for tag '{tag}'."}, 404

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
                    return {"error": "Discord rejected the message."}, 502
        except HTTPError as error:
            return {"error": f"Discord rejected the message ({error.code})."}, 502
        except URLError:
            return {"error": "Could not connect to Discord."}, 502

        return {"message": "Discord notification sent.", "tag": tag.strip()}, 200
