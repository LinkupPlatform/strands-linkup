"""Tests for the Linkup tools."""

import datetime
import json
from typing import Any
from unittest.mock import MagicMock

import pytest
from linkup import (
    LinkupAuthenticationError,
    LinkupFetchResponse,
    LinkupSearchResults,
    LinkupSourcedAnswer,
)
from strands import Agent

from strands_linkup import linkup_fetch, linkup_search

SEARCH_RESULTS = LinkupSearchResults.model_validate(
    {
        "results": [
            {
                "type": "text",
                "name": "Strands Agents",
                "url": "https://strandsagents.com",
                "content": "A model-driven approach to building AI agents.",
                "favicon": "https://strandsagents.com/favicon.ico",
            },
            {"type": "image", "name": "Strands logo", "url": "https://strandsagents.com/logo.svg"},
        ]
    }
)

SOURCED_ANSWER = LinkupSourcedAnswer.model_validate(
    {
        "answer": "Strands Agents is an open-source SDK for building AI agents.",
        "sources": [
            {
                "name": "Strands Agents",
                "url": "https://strandsagents.com",
                "snippet": "A model-driven approach to building AI agents.",
                "favicon": "https://strandsagents.com/favicon.ico",
            }
        ],
    }
)

FETCH_RESPONSE = LinkupFetchResponse.model_validate(
    {"markdown": "# Strands Agents\n\nBuild agents.", "favicon": ""}
)


def _payload(result: dict[str, Any]) -> Any:
    assert result["status"] == "success"
    return json.loads(result["content"][0]["text"])


def _error_text(result: dict[str, Any]) -> str:
    assert result["status"] == "error"
    text: str = result["content"][0]["text"]
    return text


# Tool registration


def test_tools_are_registered() -> None:
    assert linkup_search.tool_name == "linkup_search"
    assert linkup_fetch.tool_name == "linkup_fetch"


def test_search_tool_spec() -> None:
    schema = linkup_search.tool_spec["inputSchema"]["json"]
    assert schema["required"] == ["query"]
    assert schema["properties"]["depth"]["enum"] == ["flash", "fast", "standard", "deep"]
    assert schema["properties"]["output_type"]["enum"] == ["searchResults", "sourcedAnswer"]
    assert set(schema["properties"]) == {
        "query",
        "depth",
        "output_type",
        "include_domains",
        "exclude_domains",
        "from_date",
        "to_date",
        "max_results",
    }


def test_fetch_tool_spec() -> None:
    schema = linkup_fetch.tool_spec["inputSchema"]["json"]
    assert schema["required"] == ["url"]
    assert set(schema["properties"]) == {"url", "render_js"}


# linkup_search


async def test_search_results(mock_client: MagicMock) -> None:
    mock_client.async_search.return_value = SEARCH_RESULTS

    result = await linkup_search(query="What is Strands Agents?")

    assert _payload(result) == {
        "results": [
            {
                "type": "text",
                "name": "Strands Agents",
                "url": "https://strandsagents.com",
                "content": "A model-driven approach to building AI agents.",
            },
            {"type": "image", "name": "Strands logo", "url": "https://strandsagents.com/logo.svg"},
        ]
    }
    mock_client.client_class.assert_called_once_with(api_key="test-api-key")
    mock_client.async_search.assert_awaited_once_with(
        query="What is Strands Agents?",
        depth="standard",
        output_type="searchResults",
        include_domains=None,
        exclude_domains=None,
        from_date=None,
        to_date=None,
        max_results=None,
        timeout=120.0,
    )


async def test_search_sourced_answer(mock_client: MagicMock) -> None:
    mock_client.async_search.return_value = SOURCED_ANSWER

    result = await linkup_search(query="What is Strands Agents?", output_type="sourcedAnswer")

    assert _payload(result) == {
        "answer": "Strands Agents is an open-source SDK for building AI agents.",
        "sources": [
            {
                "name": "Strands Agents",
                "url": "https://strandsagents.com",
                "snippet": "A model-driven approach to building AI agents.",
            }
        ],
    }
    assert mock_client.async_search.call_args.kwargs["output_type"] == "sourcedAnswer"


async def test_search_passes_all_parameters(mock_client: MagicMock) -> None:
    mock_client.async_search.return_value = SEARCH_RESULTS

    await linkup_search(
        query="AI agent frameworks",
        depth="deep",
        include_domains=["github.com"],
        exclude_domains=["example.com"],
        from_date="2026-01-01",
        to_date="2026-06-30",
        max_results=5,
    )

    mock_client.async_search.assert_awaited_once_with(
        query="AI agent frameworks",
        depth="deep",
        output_type="searchResults",
        include_domains=["github.com"],
        exclude_domains=["example.com"],
        from_date=datetime.date(2026, 1, 1),
        to_date=datetime.date(2026, 6, 30),
        max_results=5,
        timeout=120.0,
    )


@pytest.mark.parametrize("query", ["", "   "])
async def test_search_empty_query(mock_client: MagicMock, query: str) -> None:
    result = await linkup_search(query=query)

    assert "Query parameter is required" in _error_text(result)
    mock_client.async_search.assert_not_awaited()


async def test_search_invalid_max_results(mock_client: MagicMock) -> None:
    result = await linkup_search(query="test", max_results=0)

    assert "max_results must be at least 1" in _error_text(result)
    mock_client.async_search.assert_not_awaited()


@pytest.mark.parametrize("field", ["from_date", "to_date"])
async def test_search_invalid_date(mock_client: MagicMock, field: str) -> None:
    result = await linkup_search(query="test", **{field: "01/02/2026"})

    assert f"Invalid date format for {field}" in _error_text(result)
    mock_client.async_search.assert_not_awaited()


async def test_search_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LINKUP_API_KEY", raising=False)

    result = await linkup_search(query="test")

    assert "LINKUP_API_KEY environment variable is required" in _error_text(result)


async def test_search_api_error(mock_client: MagicMock) -> None:
    mock_client.async_search.side_effect = LinkupAuthenticationError("Invalid API key")

    result = await linkup_search(query="test")

    assert _error_text(result) == (
        "Linkup search failed (LinkupAuthenticationError): Invalid API key"
    )


# linkup_fetch


async def test_fetch(mock_client: MagicMock) -> None:
    mock_client.async_fetch.return_value = FETCH_RESPONSE

    result = await linkup_fetch(url="https://strandsagents.com")

    assert _payload(result) == {
        "url": "https://strandsagents.com",
        "markdown": "# Strands Agents\n\nBuild agents.",
    }
    mock_client.async_fetch.assert_awaited_once_with(
        url="https://strandsagents.com", render_js=False, timeout=120.0
    )


async def test_fetch_render_js(mock_client: MagicMock) -> None:
    mock_client.async_fetch.return_value = FETCH_RESPONSE

    await linkup_fetch(url="https://strandsagents.com", render_js=True)

    assert mock_client.async_fetch.call_args.kwargs["render_js"] is True


async def test_fetch_empty_url(mock_client: MagicMock) -> None:
    result = await linkup_fetch(url="")

    assert "URL parameter is required" in _error_text(result)
    mock_client.async_fetch.assert_not_awaited()


async def test_fetch_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LINKUP_API_KEY", raising=False)

    result = await linkup_fetch(url="https://strandsagents.com")

    assert "LINKUP_API_KEY environment variable is required" in _error_text(result)


async def test_fetch_api_error(mock_client: MagicMock) -> None:
    mock_client.async_fetch.side_effect = RuntimeError("boom")

    result = await linkup_fetch(url="https://strandsagents.com")

    assert _error_text(result) == "Linkup fetch failed (RuntimeError): boom"


# Through a Strands agent


def test_agent_direct_tool_calls(mock_client: MagicMock) -> None:
    mock_client.async_search.return_value = SEARCH_RESULTS
    mock_client.async_fetch.return_value = FETCH_RESPONSE
    agent = Agent(tools=[linkup_search, linkup_fetch])

    search_result = agent.tool.linkup_search(query="Strands", record_direct_tool_call=False)
    fetch_result = agent.tool.linkup_fetch(
        url="https://strandsagents.com", record_direct_tool_call=False
    )

    assert search_result["status"] == "success"
    assert json.loads(search_result["content"][0]["text"])["results"][0]["name"] == "Strands Agents"
    assert fetch_result["status"] == "success"
    assert "# Strands Agents" in fetch_result["content"][0]["text"]
