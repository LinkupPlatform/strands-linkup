from collections.abc import Iterator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def linkup_api_key(monkeypatch: pytest.MonkeyPatch) -> str:
    api_key = "test-api-key"
    monkeypatch.setenv("LINKUP_API_KEY", api_key)
    return api_key


@pytest.fixture
def mock_client(linkup_api_key: str) -> Iterator[MagicMock]:
    """Patch LinkupClient so that no test reaches the network."""
    client = MagicMock()
    client.async_search = AsyncMock()
    client.async_fetch = AsyncMock()
    with patch("strands_linkup.linkup.LinkupClient", return_value=client) as client_class:
        client.client_class = client_class
        yield client
