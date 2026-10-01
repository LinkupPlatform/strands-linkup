"""Linkup web search and fetch tools for Strands Agents.

Linkup is a web search API built for AI agents. These tools give a Strands agent real-time,
citable web results and clean page content.

Usage with Strands Agent:

```python
from strands import Agent
from strands_linkup import linkup_fetch, linkup_search

agent = Agent(tools=[linkup_search, linkup_fetch])

# Let the model decide when to search
agent("What did the latest Python release add?")

# Or call the tools directly
agent.tool.linkup_search(query="Strands Agents SDK", depth="standard")
agent.tool.linkup_fetch(url="https://strandsagents.com")
```

Environment Variables:
- LINKUP_API_KEY: Your Linkup API key (required). Get one at https://app.linkup.so
"""

import json
import logging
import os
from datetime import date
from typing import Any, Literal

from linkup import (
    LinkupClient,
    LinkupFetchResponse,
    LinkupSearchImageResult,
    LinkupSearchResults,
    LinkupSourcedAnswer,
)
from strands import tool

logger = logging.getLogger(__name__)

LINKUP_API_KEY_ENV = "LINKUP_API_KEY"
# Deep searches run several retrieval iterations and can take tens of seconds.
DEFAULT_TIMEOUT_SECONDS = 120.0


def _get_client() -> LinkupClient:
    api_key = os.getenv(LINKUP_API_KEY_ENV)
    if not api_key:
        raise ValueError(
            f"{LINKUP_API_KEY_ENV} environment variable is required. "
            "Get your API key at https://app.linkup.so"
        )
    return LinkupClient(api_key=api_key)


def _parse_date(value: str | None, name: str) -> date | None:
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"Invalid date format for {name}. Use YYYY-MM-DD.") from None


def _success(payload: dict[str, Any]) -> dict[str, Any]:
    return {"status": "success", "content": [{"text": json.dumps(payload, ensure_ascii=False)}]}


def _error(message: str) -> dict[str, Any]:
    return {"status": "error", "content": [{"text": message}]}


def _format_search_results(response: LinkupSearchResults) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for result in response.results:
        if isinstance(result, LinkupSearchImageResult):
            results.append({"type": "image", "name": result.name, "url": result.url})
        else:
            results.append(
                {"type": "text", "name": result.name, "url": result.url, "content": result.content}
            )
    return {"results": results}


def _format_sourced_answer(response: LinkupSourcedAnswer) -> dict[str, Any]:
    return {
        "answer": response.answer,
        "sources": [
            {"name": source.name, "url": source.url, "snippet": source.snippet}
            for source in response.sources
        ],
    }


def _format_fetch_response(url: str, response: LinkupFetchResponse) -> dict[str, Any]:
    return {"url": url, "markdown": response.markdown}


@tool
async def linkup_search(
    query: str,
    depth: Literal["flash", "fast", "standard", "deep"] = "standard",
    output_type: Literal["searchResults", "sourcedAnswer"] = "searchResults",
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    max_results: int | None = None,
) -> dict[str, Any]:
    """Search the web in real time with Linkup and return relevant, citable sources.

    Use for current events, facts that may have changed, and anything that needs a verifiable
    source. Each result includes a title, URL, and content.

    Depths:
    - flash: lowest latency, ranked sources and snippets
    - fast: one-shot retrieval in about a second
    - standard: a single pass of agentic search; the right choice for most queries (default)
    - deep: several search iterations, for complex multi-step questions (slower)

    Output types:
    - searchResults: a list of sources with their content (default)
    - sourcedAnswer: a natural-language answer to the query plus the sources supporting it

    Args:
        query: The search query, in natural language. Example: "Latest developments in
            solid-state batteries"
        depth: Search depth - "flash", "fast", "standard" (default), or "deep"
        output_type: "searchResults" (default) for raw sources, or "sourcedAnswer" for an
            answer with sources
        include_domains: Only return results from these domains (e.g. ["arxiv.org"])
        exclude_domains: Never return results from these domains
        from_date: Only include results published on or after this date (YYYY-MM-DD)
        to_date: Only include results published on or before this date (YYYY-MM-DD)
        max_results: Maximum number of results to return

    Returns:
        Dict with status and content. On success, the content text is JSON: {"results": [...]}
        for searchResults, or {"answer": ..., "sources": [...]} for sourcedAnswer.
    """
    try:
        if not query or not query.strip():
            return _error("Query parameter is required and cannot be empty")
        if max_results is not None and max_results < 1:
            return _error("max_results must be at least 1")

        parsed_from_date = _parse_date(from_date, "from_date")
        parsed_to_date = _parse_date(to_date, "to_date")
        client = _get_client()

        logger.info("Making Linkup search request for query: %s", query)
        response = await client.async_search(
            query=query,
            depth=depth,
            output_type=output_type,
            include_domains=include_domains,
            exclude_domains=exclude_domains,
            from_date=parsed_from_date,
            to_date=parsed_to_date,
            max_results=max_results,
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )

        if isinstance(response, LinkupSourcedAnswer):
            return _success(_format_sourced_answer(response))
        if isinstance(response, LinkupSearchResults):
            return _success(_format_search_results(response))
        return _error(f"Unexpected Linkup response type: {type(response).__name__}")

    except ValueError as e:
        return _error(str(e))
    except Exception as e:
        logger.error("Linkup search failed: %s", e)
        return _error(f"Linkup search failed ({type(e).__name__}): {e}")


@tool
async def linkup_fetch(url: str, render_js: bool = False) -> dict[str, Any]:
    """Fetch a web page with Linkup and return its content as clean markdown.

    Use when you already know the URL and need the full page content, for example to read a
    source returned by linkup_search.

    Args:
        url: The URL of the web page to fetch. Example: "https://docs.linkup.so"
        render_js: Render the page's JavaScript before extracting content. Slower; enable it
            for single-page apps or pages that load their content dynamically.

    Returns:
        Dict with status and content. On success, the content text is JSON:
        {"url": ..., "markdown": ...}.
    """
    try:
        if not url or not url.strip():
            return _error("URL parameter is required and cannot be empty")

        client = _get_client()

        logger.info("Making Linkup fetch request for URL: %s", url)
        response = await client.async_fetch(
            url=url,
            render_js=render_js,
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )
        return _success(_format_fetch_response(url, response))

    except ValueError as e:
        return _error(str(e))
    except Exception as e:
        logger.error("Linkup fetch failed: %s", e)
        return _error(f"Linkup fetch failed ({type(e).__name__}): {e}")
