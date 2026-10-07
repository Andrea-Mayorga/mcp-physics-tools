"""Week 5 Meeting 1 — Minimal LLM Client for the MCP Physics Server

This script starts mcp_skeleton.py as a subprocess, connects to it over
stdio, and sends a compound physics query that requires both tools.

Expected output: the LLM chains query_simbad and search_arxiv and returns
a coherent paragraph about Betelgeuse's spectral type, parallax, and recent
arXiv papers discussing its evolutionary status.

Usage:
    python llm_client.py

Requirements:
    pip install mcp anthropic python-dotenv
    ANTHROPIC_API_KEY set in a .env file (never hardcode it here)
"""

import asyncio
import json
import os
import sys
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()

SERVER_SCRIPT = Path(__file__).parent / "mcp_skeleton.py"
QUERY = (
    "What is the spectral type of Betelgeuse and what are the 3 most recent "
    "arXiv papers about it?"
)


def _tool_schemas(tools) -> list[dict]:
    """Convert MCP tool descriptors to the Anthropic tools format."""
    return [
        {
            "name": t.name,
            "description": t.description or "",
            "input_schema": t.input_schema,  # mcp 2.x name (was inputSchema)
        }
        for t in tools
    ]


async def run():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("ANTHROPIC_API_KEY not set. Add it to a .env file.")

    client = anthropic.Anthropic(api_key=api_key)
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_SCRIPT)],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tool_list = (await session.list_tools()).tools
            schemas = _tool_schemas(tool_list)

            print(f"Connected — {len(tool_list)} tool(s) available: "
                  f"{[t.name for t in tool_list]}\n")
            print(f"Query: {QUERY}\n{'='*60}")

            messages = [{"role": "user", "content": QUERY}]

            # Agentic loop: keep going until the model stops calling tools
            while True:
                response = client.messages.create(
                    model="claude-sonnet-5-5",
                    max_tokens=1024,
                    tools=schemas,
                    messages=messages,
                )

                # Collect the assistant turn (may mix text and tool_use blocks)
                messages.append({"role": "assistant", "content": response.content})

                if response.stop_reason == "end_turn":
                    # Final answer — print and exit
                    for block in response.content:
                        if hasattr(block, "text"):
                            print("\nFinal answer:\n", block.text)
                    break

                if response.stop_reason != "tool_use":
                    print(f"Unexpected stop_reason: {response.stop_reason}")
                    break

                # Execute all tool calls the model requested
                tool_results = []
                for block in response.content:
                    if block.type != "tool_use":
                        continue

                    print(f"\n[Tool call] {block.name}({json.dumps(block.input)})")
                    mcp_result = await session.call_tool(block.name, block.input)

                    # Flatten MCP content list to a single JSON string.
                    # A tool that returns a list (search_arxiv) arrives as one
                    # content block per item, so join them all, not just [0].
                    if mcp_result.content:
                        result_text = "\n".join(
                            raw.text if hasattr(raw, "text")
                            else json.dumps(getattr(raw, "json", str(raw)))
                            for raw in mcp_result.content
                        )
                    else:
                        result_text = "null"

                    print(f"[Tool result] {result_text[:200]}"
                          f"{'...' if len(result_text) > 200 else ''}")

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_text,
                    })

                messages.append({"role": "user", "content": tool_results})


if __name__ == "__main__":
    asyncio.run(run())
