# MCP Physics Tools

An MCP server exposing two physics database queries as tools that an LLM (Claude) can call:
- `query_simbad`: object type, spectral type, parallax, and radial velocity from SIMBAD
- `search_arxiv`: recent arXiv papers matching a keyword

Class practice for the AI for Physics course, Week 5.

## Setup
```bash
conda env create -f environment.yml
conda activate mcp-physics
cp .env.example .env   # then add your ANTHROPIC_API_KEY to .env
```

## Usage
```bash
python mcp_skeleton.py --test   # test the tools directly (no API calls)
python llm_client.py            # Claude calls the tools (uses API credits)
```

`llm_client.py` starts the server automatically, so there's no need to run `mcp_skeleton.py` separately.

## Tested versions (2026-10-07)
- Python 3.11, `mcp` 2.2.0, `astroquery` 0.4.11, `arxiv` 4.0.1, `anthropic` 1.8.0
- Model: `claude-sonnet-5-5`

## Notes
- Updated for `mcp` 2.x: `MCPServer` instead of `Server`, `run_stdio_async()`, and `input_schema` instead of `inputSchema`.
- `llm_client.py` joins all content blocks of a tool result, since list results (e.g. `search_arxiv`) arrive as one block per item.
- SIMBAD currently returns Betelgeuse's spectral type as `M1-M2Ia-Iab` (formerly `M1-2Ia-Iab`): same classification, different notation.
