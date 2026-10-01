"""A research agent that answers questions with cited, up-to-date web sources.

Requirements:
- LINKUP_API_KEY set in the environment (https://app.linkup.so)
- Credentials for the model provider used by Strands (Amazon Bedrock by default)

Run with:
    python examples/research_agent.py "What changed in the latest Python release?"
"""

import sys

from strands import Agent

from strands_linkup import linkup_fetch, linkup_search

SYSTEM_PROMPT = """You are a research assistant.
- Use linkup_search to find current information on the web before answering.
- Use linkup_fetch to read a page in full when a search result looks relevant but incomplete.
- Cite the URL of every source you rely on.
"""


def main() -> None:
    question = " ".join(sys.argv[1:]) or "What are the latest developments in AI agent frameworks?"
    agent = Agent(system_prompt=SYSTEM_PROMPT, tools=[linkup_search, linkup_fetch])
    agent(question)


if __name__ == "__main__":
    main()
