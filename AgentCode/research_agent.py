# AgentCode/research_agent.py
"""
LangGraph-compatible research agent shim.

Exposes:
  run_analysis(mode='stub'|'real', sector=None, subsector=None, prompt=None) -> dict

Behavior:
- mode == 'stub' returns deterministic mock response
- mode == 'real' will attempt:
    1. to call a Python LangGraph SDK (if configured) via _call_langgraph_sdk()
    2. otherwise to call a CLI-based langgraph command via _call_langgraph_cli()
- Normalizes outputs to {"overview":..., "Companies": {...}, "sector":..., "subsector":..., "raw":...}
- Uses a simple file TTL cache to avoid expensive repeated runs.
"""

import os
import json
import hashlib
import pathlib
import subprocess
import sys
import traceback
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# ===== CONFIG =====
CACHE_DIR = os.environ.get('RESEARCH_CACHE_DIR', './.research_cache')
CACHE_TTL_SECONDS = int(os.environ.get('RESEARCH_CACHE_TTL', str(60 * 60 * 6)))  # 6 hours
LANGGRAPH_PY_SDK_AVAILABLE = os.environ.get('LANGGRAPH_PY_SDK_AVAILABLE', 'false').lower() in ('1','true','yes')
LANGGRAPH_GRAPH_PATH = os.environ.get('LANGGRAPH_GRAPH_PATH', 'graph.json')
LANGGRAPH_CLI_CMD = os.environ.get('LANGGRAPH_CLI_CMD', f'langgraph run --graph {LANGGRAPH_GRAPH_PATH}')
os.makedirs(CACHE_DIR, exist_ok=True)

# ===== Helpers: cache =====
def _cache_key_for_inputs(mode: str, sector: Optional[str], subsector: Optional[str], prompt: Optional[str]) -> str:
    payload = json.dumps({
        'mode': mode,
        'sector': sector or '',
        'subsector': subsector or '',
        'prompt': prompt or ''
    }, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()

def _load_from_cache(key: str) -> Optional[Dict[str, Any]]:
    path = pathlib.Path(CACHE_DIR) / f"{key}.json"
    if not path.exists():
        return None
    try:
        meta = json.loads(path.read_text(encoding='utf-8'))
        ts = datetime.fromisoformat(meta.get('_cached_at'))
        if (datetime.utcnow() - ts).total_seconds() > CACHE_TTL_SECONDS:
            path.unlink(missing_ok=True)
            return None
        return meta.get('payload')
    except Exception:
        try:
            path.unlink(missing_ok=True)
        except Exception:
            pass
        return None

def _write_to_cache(key: str, payload: Dict[str, Any]):
    path = pathlib.Path(CACHE_DIR) / f"{key}.json"
    wrapped = {'_cached_at': datetime.utcnow().isoformat(), 'payload': payload}
    try:
        path.write_text(json.dumps(wrapped, default=str), encoding='utf-8')
    except Exception:
        pass

# ===== Helpers: robust LLM call =====
def _safe_llm_call(llm, prompt: str, **kwargs) -> str:
    """
    Attempt popular invocation patterns and return textual result (best-effort).
    Replace/extend per your LLM client specifics.
    """
    try:
        if hasattr(llm, "invoke"):
            r = llm.invoke(prompt, **kwargs)
            return getattr(r, "content", None) or getattr(r, "text", None) or str(r)
        if callable(llm):
            try:
                r = llm(prompt)
            except TypeError:
                r = llm({"input": prompt})
            return getattr(r, "content", None) or getattr(r, "text", None) or str(r)
        if hasattr(llm, "generate"):
            r = llm.generate([prompt])
            # many libs store text under r.generations[0][0].text
            try:
                return r.generations[0][0].text
            except Exception:
                return str(r)
    except Exception:
        return f"[LLM_CALL_FAILED] {traceback.format_exc()}"
    return ""

# ===== LangGraph integration points =====
def _call_langgraph_sdk(graph_path: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Replace this pseudocode with your LangGraph Python SDK usage (if available).
    Example:
      from langgraph import Pipeline
      pipeline = Pipeline.from_file(graph_path)
      result = pipeline.run(inputs)
      return result
    """
    raise NotImplementedError("LangGraph Python SDK path not implemented in this template.")

def _call_langgraph_cli(graph_path: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fallback CLI invocation. Ensure your langgraph CLI accepts JSON on stdin and returns JSON on stdout.
    If your CLI differs, adjust LANGGRAPH_CLI_CMD or this function.
    """
    cmd = LANGGRAPH_CLI_CMD.split()
    if '--graph' not in cmd and graph_path:
        cmd += ['--graph', graph_path]
    try:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdin_payload = json.dumps(inputs)
        stdout, stderr = proc.communicate(stdin_payload, timeout=300)
        if proc.returncode != 0:
            raise RuntimeError(f"LangGraph CLI failed: {stderr.strip()}")
        return json.loads(stdout)
    except Exception as e:
        raise

# ===== Stub generator =====
def _stub_result(sector: Optional[str], subsector: Optional[str], prompt: Optional[str]) -> Dict[str, Any]:
    companies = {
        "MRF": {
            "Market Share": "20%",
            "Products Manufactured": "Tyres",
            "Key Raw Materials": "Natural Rubber, Carbon Black"
        },
        "JKTYRE": {
            "Market Share": "10%",
            "Products Manufactured": "Tyres",
            "Key Raw Materials": "Synthetic Rubber, Steel"
        }
    }
    return {
        "overview": f"[STUB] Summary for {sector or 'Generic sector'} / {subsector or 'all'}",
        "sector": sector or "",
        "subsector": subsector or "",
        "Companies": companies,
        "prompt_used": prompt or ""
    }

# ===== Public API =====
def run_analysis(mode: str = 'stub', sector: Optional[str] = None, subsector: Optional[str] = None,
                 prompt: Optional[str] = None, use_cache: bool = True) -> Dict[str, Any]:
    """
    Main entrypoint used by server.py
    Returns a normalized dict with keys: overview, Companies, sector, subsector, raw
    """
    mode = (mode or 'stub').lower()
    sector = sector or ""
    subsector = subsector or ""
    prompt = prompt or ""

    cache_key = _cache_key_for_inputs(mode, sector, subsector, prompt)
    if use_cache:
        cached = _load_from_cache(cache_key)
        if cached is not None:
            return cached

    # stub faster path
    if mode == 'stub':
        res = _stub_result(sector, subsector, prompt)
        if use_cache:
            _write_to_cache(cache_key, res)
        return res

    # real mode
    inputs = {"sector": sector, "subsector": subsector, "prompt": prompt, "timestamp": datetime.utcnow().isoformat()}
    result = None
    # Try SDK first (if configured)
    if LANGGRAPH_PY_SDK_AVAILABLE:
        try:
            result = _call_langgraph_sdk(LANGGRAPH_GRAPH_PATH, inputs)
        except Exception:
            result = None

    # Fallback to CLI
    if result is None:
        try:
            result = _call_langgraph_cli(LANGGRAPH_GRAPH_PATH, inputs)
        except Exception as exc:
            # Return a safe error structure
            err = {
                "overview": "",
                "Companies": {},
                "sector": sector,
                "subsector": subsector,
                "raw": None,
                "error": f"LangGraph invocation failed: {str(exc)}",
                "error_stack": traceback.format_exc()
            }
            if use_cache:
                _write_to_cache(cache_key, err)
            return err

    # Normalize result into expected shape
    normalized = {"sector": sector, "subsector": subsector, "overview": "", "Companies": {}, "raw": result}
    # If result already contains keys, use them
    if isinstance(result, dict):
        if 'overview' in result or 'Companies' in result:
            normalized['overview'] = result.get('overview', '')
            normalized['Companies'] = result.get('Companies', {}) or {}
            normalized['raw'] = result
        else:
            # Try to detect assistant_response or similar
            if 'assistant_response' in result:
                try:
                    parsed = json.loads(result['assistant_response'])
                    if isinstance(parsed, dict):
                        normalized['overview'] = parsed.get('overview', '')
                        normalized['Companies'] = parsed.get('Companies', {})
                        normalized['raw'] = parsed
                except Exception:
                    normalized['overview'] = str(result.get('assistant_response'))
            else:
                # Fallback: put stringified result in raw
                normalized['raw'] = result

    if use_cache:
        _write_to_cache(cache_key, normalized)
    return normalized
