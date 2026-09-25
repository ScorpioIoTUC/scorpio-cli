import unittest
from http import HTTPStatus
from unittest.mock import Mock

from scorpio.server.main import Handler


class ScorpioApiSettingsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.handler = Handler.__new__(Handler)
        self.handler.storage_handler = Mock()
        self.handler.storage_handler.get.return_value = {"other": "preserved"}
        self.handler.remote_executor = Mock()
        self.handler.remote_executor.is_connected = True

    def test_packets_path_is_removed_from_base_url(self) -> None:
        result = self.handler._normalize_api_base_url(
            "http://192.168.1.111:3000/packets/"
        )

        self.assertEqual(result, "http://192.168.1.111:3000")

    def test_settings_update_recreates_data_export(self) -> None:
        self.handler.remote_executor.stream.side_effect = [
            iter(["Container data-export recreated"]),
            iter(
                [
                    "SCORPIO_API_URL=http://192.168.1.111:3000",
                    "SCORPIO_STATION_KEY=station-id.station-key",
                ]
            ),
        ]

        payload, status = self.handler._set_setup_token(
            {
                "api_url": "http://192.168.1.111:3000/packets",
                "token": "station-id.station-key",
            }
        )

        update_command = self.handler.remote_executor.stream.call_args_list[0].args[0]
        self.assertIn("SCORPIO_API_URL=http://192.168.1.111:3000", update_command)
        self.assertIn("SCORPIO_STATION_KEY=station-id.station-key", update_command)
        self.assertIn("--force-recreate data_export", update_command)
        self.handler.storage_handler.update.assert_called_once_with(
            {
                "other": "preserved",
                "token_config": {
                    "api_url": "http://192.168.1.111:3000",
                    "token": "station-id.station-key",
                },
            }
        )
        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(
            payload["message"],
            "API settings updated and data-export restarted.",
        )

    def test_invalid_url_does_not_execute_remote_command(self) -> None:
        payload, status = self.handler._set_setup_token(
            {"api_url": "localhost:3000", "token": "station-id.station-key"}
        )

        self.handler.remote_executor.stream.assert_not_called()
        self.assertEqual(status, HTTPStatus.BAD_REQUEST)
        self.assertIn("valid API base URL", payload["error"])


if __name__ == "__main__":
    unittest.main()
