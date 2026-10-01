# ⚡ Strands Linkup

[![PyPI version](https://badge.fury.io/py/strands-linkup.svg)](https://pypi.org/project/strands-linkup/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[Linkup](https://www.linkup.so) web search and fetch tools for
[Strands Agents](https://strandsagents.com). Give your agent real-time, citable web results and
clean page content in two lines. 🔗

## 🌟 Features

- 🔍 **`linkup_search`**: real-time web search returning sources (title, URL, content) or a
  sourced answer.
- 📄 **`linkup_fetch`**: fetch any URL as clean markdown, with optional JavaScript rendering.
- 🎚️ **Four search depths**: from `flash` (lowest latency) to `deep` (multi-step agentic search).
- 🧭 **Filters**: include/exclude domains, date ranges, and result limits.
- ⚡ **Async-native**: both tools are async `@tool` functions that run concurrently with the rest of
  your agent's tool calls.

## 📦 Installation

```bash
pip install strands-linkup
```

## 🛠️ Usage

### Setting Up Your Environment

1. **🔑 Obtain an API Key:** sign up at [app.linkup.so](https://app.linkup.so) to get your API key.

2. **⚙️ Set the API Key:** export the `LINKUP_API_KEY` environment variable before running your
   agent (or set it with `os.environ` / a `.env` file loaded by
   [python-dotenv](https://github.com/theskumar/python-dotenv)).

   ```bash
   export LINKUP_API_KEY='YOUR_LINKUP_API_KEY'
   ```

### Quickstart

```python
from strands import Agent
from strands_linkup import linkup_fetch, linkup_search

agent = Agent(tools=[linkup_search, linkup_fetch])
agent("What are the latest developments in solid-state batteries? Cite your sources.")
```

The agent uses whichever model you configure for Strands (Amazon Bedrock by default). See the
[Strands model providers docs](https://strandsagents.com/docs/user-guide/concepts/model-providers/)
to use another provider.

### Calling the tools directly

Strands lets you call a tool directly, without going through the model:

```python
result = agent.tool.linkup_search(
    query="Strands Agents SDK release notes",
    depth="standard",
    max_results=5,
)

answer = agent.tool.linkup_search(
    query="Who won the 2026 Tour de France?",
    output_type="sourcedAnswer",
)

page = agent.tool.linkup_fetch(url="https://docs.linkup.so", render_js=False)
```

## 📋 Tools

Both tools return the standard Strands tool result shape:
`{"status": "success" | "error", "content": [{"text": "..."}]}`. On success, the text is JSON.

### `linkup_search`

| Parameter         | Type        | Default           | Description                                                                 |
|-------------------|-------------|-------------------|-----------------------------------------------------------------------------|
| `query`           | `str`       | required          | The search query, in natural language.                                     |
| `depth`           | `str`       | `"standard"`      | `"flash"`, `"fast"`, `"standard"` or `"deep"`.                             |
| `output_type`     | `str`       | `"searchResults"` | `"searchResults"` for raw sources, `"sourcedAnswer"` for an answer + sources. |
| `include_domains` | `list[str]` | `None`            | Only return results from these domains.                                    |
| `exclude_domains` | `list[str]` | `None`            | Never return results from these domains.                                   |
| `from_date`       | `str`       | `None`            | Only results published on or after this date (`YYYY-MM-DD`).               |
| `to_date`         | `str`       | `None`            | Only results published on or before this date (`YYYY-MM-DD`).              |
| `max_results`     | `int`       | `None`            | Maximum number of results to return.                                       |

Output JSON:

- `searchResults`: `{"results": [{"type": "text", "name": ..., "url": ..., "content": ...}, ...]}`
- `sourcedAnswer`: `{"answer": ..., "sources": [{"name": ..., "url": ..., "snippet": ...}, ...]}`

Choosing a depth:

- `flash`: lowest latency, ranked sources and snippets.
- `fast`: one-shot retrieval in about a second.
- `standard`: a single pass of agentic search, the right choice for most queries.
- `deep`: several search iterations for complex, multi-step questions. Slower (can take 5-30s).

### `linkup_fetch`

| Parameter   | Type   | Default  | Description                                                    |
|-------------|--------|----------|----------------------------------------------------------------|
| `url`       | `str`  | required | The URL of the web page to fetch.                              |
| `render_js` | `bool` | `False`  | Render the page's JavaScript before extracting content.        |

Output JSON: `{"url": ..., "markdown": ...}`

## 📚 More Examples

See the [`examples/`](examples) directory for a runnable research agent.

## 🧑‍💻 Development

```bash
make install-dev   # install dependencies and pre-commit hooks
make test          # lint, type-check and run unit tests
```

## 🔗 Resources

- [Linkup documentation](https://docs.linkup.so)
- [Linkup API keys](https://app.linkup.so)
- [Strands Agents documentation](https://strandsagents.com)
- [Strands custom tools](https://strandsagents.com/docs/user-guide/concepts/tools/custom-tools/)

## 📄 License

MIT. See [LICENSE](LICENSE).
