import socket

import pytest


@pytest.fixture(autouse=True)
def offline_test_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    # Prevent tests from loading credentials or opening sockets.
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("PYTHON_DOTENV_DISABLED", "1")

    def deny_network(*args: object, **kwargs: object) -> None:
        raise AssertionError("offline tests must not use the network")

    monkeypatch.setattr(socket, "create_connection", deny_network)
    monkeypatch.setattr(socket.socket, "connect", deny_network)