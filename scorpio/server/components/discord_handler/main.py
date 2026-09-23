"""Compatibility facade for the former DiscordHandler import."""

from scorpio.server.application.contracts.ports import Storage
from scorpio.server.application.use_cases.discord import DiscordUseCases
from scorpio.server.http.controllers import to_http
from scorpio.server.infrastructure.discord_delivery import DiscordHttpDelivery


class DiscordHandler:
    def __init__(self, storage_handler: Storage) -> None:
        self.use_cases = DiscordUseCases(
            storage_handler, DiscordHttpDelivery()
        )

    def get_settings(self):
        return self.use_cases.get_settings()

    def setup(self, token):
        return to_http(self.use_cases.setup(token))

    def set_channel(self, tag, channel_id):
        return to_http(self.use_cases.set_channel(tag, channel_id))

    def set_alert_gap(self, minutes):
        return to_http(self.use_cases.set_alert_gap(minutes))

    def remove(self):
        return to_http(self.use_cases.remove())

    def notify(self, message, tag):
        return to_http(self.use_cases.notify(message, tag))
