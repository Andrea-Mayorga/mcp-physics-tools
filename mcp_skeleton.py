"""Week 5 Meeting 1 — MCP Server Skeleton

Implement a minimal MCP server that exposes two physics database queries
as LLM-callable tools.

Goal: by the end of this exercise your server should return
      spectral type 'M1-2Ia-Iab' for Betelgeuse.

Steps:
  1. Implement query_simbad() using astroquery.simbad
  2. Implement search_arxiv() using the arxiv library
  3. Test each tool in isolation with the __main__ block below
  4. Run this server and invoke both tools via llm_client.py

Start the server:
    python mcp_skeleton.py

Then, in a separate terminal:
    python llm_client.py
"""

# Install dependencies if needed:
#   pip install mcp astroquery arxiv anthropic python-dotenv

import asyncio
import json
import arxiv
from mcp.server import MCPServer


server = MCPServer("physics-tools")


@server.tool()
async def query_simbad(object_name: str) -> dict:
    """Query SIMBAD for basic properties of a named astronomical object.
    Returns a dict with keys: object_type, spectral_type, parallax_mas,
    radial_velocity_km_s.
    Raises ValueError if the object is not found in SIMBAD.
    """
    
    # Extra: creo mi propia instancia (zimbad) en cada llamada, en
    # vez de modificar la clase Simbad, para que las columnas 
    # no se acumulen repetidas entre llamadas al servidor.
    from astroquery.simbad import Simbad
    zimbad = Simbad()
    zimbad.add_votable_fields("sp_type", "plx_value", "rvz_radvel", "otype") 
    result_table = zimbad.query_object(object_name)
    if result_table is None or len(result_table) == 0 :
        raise ValueError(f"Object not found in SIMBAD: {object_name}")
    row = result_table[0]
    return {"object_type" : str(row["otype"]),
            "spectral_type" : str(row["sp_type"]),
            "parallax_mas": float(row["plx_value"]),
            "radial_velocity_km_s" : float(row["rvz_radvel"])}


@server.tool()
async def search_arxiv(keyword: str, max_results: int = 5) -> list:
    """Search arXiv for recent papers matching a keyword.

    Returns a list of dicts, each with keys:
    arxiv_id, title, authors, abstract.
    """
    # implement using the arxiv library


    client = arxiv.Client()
    search = arxiv.Search(
        query=keyword,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
    )
    return [
           {
               "arxiv_id": r.get_short_id(),
               "title": r.title,
               "authors": [a.name for a in r.authors],
               "abstract": r.summary,
           }
           for r in client.results(search)
       ]
    #raise NotImplementedError("Implement search_arxiv using the arxiv library")


async def _test_tools():
    """Quick smoke tests — run before connecting the LLM client."""
    print("--- Testing query_simbad ---")
    result = await query_simbad("Betelgeuse")
    assert "spectral_type" in result, "Missing spectral_type key"
    print(json.dumps(result, indent=2))

    print("\n--- Testing search_arxiv ---")
    results = await search_arxiv("Betelgeuse", max_results=3)
    assert isinstance(results, list) and len(results) > 0, "Expected a non-empty list"
    print(f"{len(results)} result(s). First title: {results[0]['title']}")


async def _serve():
        await server.run_stdio_async()


if __name__ == "__main__":
    import sys

    if "--test" in sys.argv:
        asyncio.run(_test_tools())
    else:
        asyncio.run(_serve())
