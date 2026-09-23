"""Discord settings, validation and notification orchestration."""

from typing import Any

from ..contracts.ports import DiscordDelivery, Storage
from ..contracts.result import Outcome, Result


class DiscordUseCases:
    """Persist and expose the Discord bot configuration."""

    def __init__(
        self, storage_handler: Storage, delivery: DiscordDelivery
    ) -> None:
        self.storage_handler = storage_handler
        self.delivery = delivery

    def get_settings(self) -> dict[str, Any]:
        """Return Discord settings without exposing the bot token."""
        discord = self.storage_handler.get().get("discord", {})
        return {
            "configured": bool(discord.get("auth_token")),
            "channels": discord.get("channels", {}),
            "error_alert_gap_minutes": discord.get(
                "error_alert_gap_minutes", 5
            ),
        }

    def setup(self, token: str | None) -> Result:
        """Create or replace the bot authentication token."""
        if not token or not token.strip():
            return {"error": "Discord token is required."}, Outcome.BAD_REQUEST

        storage = self.storage_handler.get()
        discord = storage.setdefault("discord", {})
        discord["auth_token"] = token.strip()
        discord.setdefault("channels", {})
        discord.setdefault("error_alert_gap_minutes", 5)
        self.storage_handler.update(storage)
        return {
            "message": "Discord token updated.",
            "configured": True,
        }, Outcome.OK

    def set_channel(self, tag: str | None, channel_id: str | None) -> Result:
        """Create or update a channel mapping by tag."""
        if (
            not tag
            or not tag.strip()
            or not channel_id
            or not channel_id.strip()
        ):
            return {
                "error": "Tag and channel_id are required."
            }, Outcome.BAD_REQUEST

        storage = self.storage_handler.get()
        discord = storage.setdefault("discord", {})
        channels = discord.setdefault("channels", {})
        channels[tag.strip()] = channel_id.strip()
        self.storage_handler.update(storage)
        return {
            "message": "Discord channel updated.",
            "channels": channels,
        }, Outcome.OK

    def set_alert_gap(self, minutes: Any) -> Result:
        """Set the minimum interval between error alerts."""
        try:
            gap = int(minutes)
            if gap < 1:
                raise ValueError
        except (TypeError, ValueError):
            return {
                "error": "minutes must be a positive integer."
            }, Outcome.BAD_REQUEST

        storage = self.storage_handler.get()
        discord = storage.setdefault("discord", {})
        discord["error_alert_gap_minutes"] = gap
        self.storage_handler.update(storage)
        return {
            "message": "Discord alert interval updated.",
            "minutes": gap,
        }, Outcome.OK

    def remove(self) -> Result:
        """Remove every Discord setting from the storage."""
        storage = self.storage_handler.get()
        storage.pop("discord", None)
        self.storage_handler.update(storage)
        return {
            "message": "Discord configuration removed.",
            "configured": False,
        }, Outcome.OK

    def notify(self, message: str | None, tag: str | None) -> Result:
        """Send a message to the Discord channel mapped by tag."""
        if not message or not message.strip() or not tag or not tag.strip():
            return {
                "error": "Message and tag are required."
            }, Outcome.BAD_REQUEST

        discord = self.storage_handler.get().get("discord", {})
        token = discord.get("auth_token")
        channel_id = discord.get("channels", {}).get(tag.strip())
        if not token:
            return {
                "error": "Discord bot is not configured."
            }, Outcome.BAD_REQUEST
        if not channel_id:
            return {
                "error": f"No Discord channel configured for tag '{tag}'."
            }, Outcome.NOT_FOUND

        error = self.delivery.send(token, channel_id, message)
        if error:
            return {"error": error}, Outcome.BAD_GATEWAY

        return {
            "message": "Discord notification sent.",
            "tag": tag.strip(),
        }, Outcome.OK
