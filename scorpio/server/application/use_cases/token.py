"""Token application operations, independent of HTTP and concrete adapters."""

from ..contracts.ports import Storage, TokenEnvironment
from ..contracts.result import Outcome, Result


class TokenUseCases:
    def __init__(
        self, storage_handler: Storage, environment: TokenEnvironment
    ) -> None:
        self.storage_handler = storage_handler
        self.environment = environment

    def get_setup_token(self) -> Result:
        storage = self.storage_handler.get()
        token_config = storage.get("token_config", {})
        if not token_config:
            return {"error": "Setup token not found."}, Outcome.NOT_FOUND
        api_url = token_config.get("api_url")
        token = token_config.get("token")
        if not api_url or not token:
            return {
                "error": "Setup token is incomplete."
            }, Outcome.INTERNAL_SERVER_ERROR

        return {
            "api_url": api_url,
            "token": token,
        }, Outcome.OK

    def set_setup_token(self, body) -> Result:
        storage = self.storage_handler.get()

        api_url = body.get("api_url")
        token = body.get("token")
        if not api_url or not token:
            return {
                "error": (
                    "Missing required fields: api_url and token are required."
                )
            }, Outcome.BAD_REQUEST
        self.environment.update(api_url, token)
        # Update the storage with the new token and api_url
        storage["token_config"] = {
            "api_url": api_url,
            "token": token,
        }
        self.storage_handler.update(storage)

        return {"message": "Setup token updated."}, Outcome.OK
