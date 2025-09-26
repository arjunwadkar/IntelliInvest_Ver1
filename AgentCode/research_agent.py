# research_agent.py

from typing import TypedDict, Literal, List
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from prompts import SECTOR_ANALYSIS_PROMPT
from prompts import SECTOR_ANALYSIS_PROMPT as _S  # keep naming consistent
from prompts import SUBSECTOR_DEEPDIVE_PROMPT
from sources import (
    get_combined_sources,
    add_dynamic_sources_for_subsector,
    get_dynamic_subsector_entry,
    is_entry_expired,
    DEFAULT_TTL_DAYS
)
import os
import re

# Tavily import guard
try:
    from tavily import TavilyClient
except Exception:
    TavilyClient = None

class AgentState(TypedDict, total=False):
    user_message: str
    assistant_response: str
    stage: Literal["sector_overview", "subsector_detail", "done"]

# Initialize LLM
llm = ChatOpenAI(model="gpt-4o-mini")

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
tavily_client = None
if TavilyClient and TAVILY_API_KEY:
    tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

def norm_key(s: str) -> str:
    k = s.lower().strip()
    k = re.sub(r"[^\w\s]", "", k)
    k = re.sub(r"\s+", "_", k)
    return k

def extract_urls_from_tavily_results(results) -> List[str]:
    urls = []
    if not results:
        return urls
    items = results.get("results") if isinstance(results, dict) else results
    if isinstance(items, dict):
        items = [items]
    if not items:
        return urls
    for it in items:
        if isinstance(it, dict):
            for key in ("url", "link", "href", "source_url"):
                if key in it and isinstance(it[key], str):
                    urls.append(it[key])
            if "document" in it and isinstance(it["document"], dict):
                maybe_url = it["document"].get("url") or it["document"].get("source")
                if isinstance(maybe_url, str):
                    urls.append(maybe_url)
            for v in it.values():
                if isinstance(v, str) and v.startswith("http"):
                    urls.append(v)
        elif isinstance(it, str) and it.startswith("http"):
            urls.append(it)
    urls = list(dict.fromkeys([u.split("#")[0] for u in urls if isinstance(u, str)]))
    return urls

def tavily_search_and_persist(sector: str, max_results: int = 5) -> List[str]:
    if not tavily_client:
        return []
    query = f"Market size, India share, subsectors, growth forecast for {sector} sector"
    try:
        if hasattr(tavily_client, "search"):
            results = tavily_client.search(query=query, max_results=max_results)
        elif hasattr(tavily_client, "query"):
            results = tavily_client.query(query=query, max_results=max_results)
        elif hasattr(tavily_client, "run"):
            results = tavily_client.run(query=query, max_results=max_results)
        else:
            results = tavily_client.search(query=query, max_results=max_results)
    except Exception:
        return []
    urls = extract_urls_from_tavily_results(results)
    if urls:
        key = norm_key(sector)
        add_dynamic_sources_for_subsector(key, urls)
    return urls

def get_relevant_sources_text(sector: str, ttl_days: int = DEFAULT_TTL_DAYS) -> str:
    combined = get_combined_sources()
    sector_key = norm_key(sector)

    refs = []

    # baseline global + india
    for url in combined.get("global", {}).get("market_research", []):
        refs.append(url)
    for url in combined.get("india", {}).get("industry_reports", []):
        refs.append(url)

    # try to find matching dynamic entry
    dynamic_entry = get_dynamic_subsector_entry(sector_key)
    matched = False
    if dynamic_entry:
        # if not expired, use it
        if not is_entry_expired(dynamic_entry, ttl_days=ttl_days):
            matched = True
            refs.extend(dynamic_entry.get("urls", []))
        else:
            # expired -> refresh via Tavily (if available)
            if tavily_client:
                new_urls = tavily_search_and_persist(sector, max_results=5)
                if new_urls:
                    matched = True
                    refs.extend(new_urls)
    # try curated subsectors
    subsectors = combined.get("subsectors", {}) or {}
    for k, urls in subsectors.items():
        if k in sector_key or sector_key in k:
            matched = True
            refs.extend(urls)

    # If nothing matched and no dynamic found -> run tavily fallback (also persists)
    if not matched and tavily_client:
        tavily_urls = tavily_search_and_persist(sector)
        refs.extend(tavily_urls)

    refs = list(dict.fromkeys([u for u in refs if u]))
    return "\n".join(refs)

def subsectors_exist_in_text(text: str) -> bool:
    if not text:
        return False
    t = text.lower()
    if "subsectors:" in t:
        parts = t.split("subsectors:", 1)
        after = parts[1]
        for line in after.splitlines():
            s = line.strip()
            if s.startswith("-") or s.startswith("*") or re.match(r"^\d+\.", s):
                if len(s) > 2 and not any(w in s for w in ("no subsectors", "none", "n/a")):
                    return True
        return False
    if any(kw in t for kw in ("subsector", "sub-sectors", "segments:", "segments")):
        return True
    return False

# Nodes
def sector_overview_node(state: AgentState):
    sector = state["user_message"]
    refs_text = get_relevant_sources_text(sector)
    full_prompt = f"""{SECTOR_ANALYSIS_PROMPT}

Additional reference URLs (for guidance, cite if relevant):
{refs_text}

Sector to analyze: {sector}
"""
    response = llm.invoke(full_prompt)
    text = response.content
    state["assistant_response"] = text
    if subsectors_exist_in_text(text):
        state["stage"] = "subsector_detail"
    else:
        state["stage"] = "done"
    return state

def subsector_detail_node(state: AgentState):
    subsector = state["user_message"]
    refs_text = get_relevant_sources_text(subsector)
    full_prompt = f"""{SUBSECTOR_DEEPDIVE_PROMPT}

Additional reference URLs (for guidance, cite if relevant):
{refs_text}

Subsector to analyze: {subsector}
"""
    response = llm.invoke(full_prompt)
    state["assistant_response"] = response.content
    state["stage"] = "done"
    return state

# Build graph
graph = StateGraph(AgentState)
graph.add_node("sector_overview", sector_overview_node)
graph.add_node("subsector_detail", subsector_detail_node)
graph.set_entry_point("sector_overview")
graph.add_edge("sector_overview", "subsector_detail")
graph.add_edge("subsector_detail", END)
app = graph.compile()