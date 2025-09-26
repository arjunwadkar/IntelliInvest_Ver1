# sources.py
import json
import os
from typing import Dict, List, Optional
from datetime import datetime, timezone

ROOT_DIR = os.path.dirname(__file__)
DYNAMIC_FILE = os.path.join(ROOT_DIR, "dynamic_sources.json")

INITIAL_SOURCES: Dict[str, Dict[str, List[str]]] = {
    "global": {
        "market_research": [
            "https://www.statista.com/",
            "https://www.imarcgroup.com/",
            "https://www.mordorintelligence.com/",
            "https://www.grandviewresearch.com/"
        ]
    },
    "india": {
        "industry_reports": [
            "https://www.ibef.org/industry",
            "https://commerce.gov.in/",
            "https://dpiit.gov.in/"
        ]
    },
    "subsectors": {
        "automotive": [
            "https://www.siam.in/",
            "https://www.acma.in/",
            "https://www.oica.net/"
        ],
        "renewable_energy": [
            "https://mnre.gov.in/",
            "https://www.iea.org/",
            "https://cea.nic.in/"
        ],
        "fintech": [
            "https://rbi.org.in/",
            "https://nasscom.in/",
            "https://www.pwc.in/industries/financial-services.html"
        ]
    }
}

# TTL default (days)
DEFAULT_TTL_DAYS = 30

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def load_dynamic_sources() -> Dict:
    """Load dynamic sources saved by the agent. Returns dict with structure:
    { "subsectors": { "<key>": { "urls": [...], "last_updated": "ISO" }, ... } }
    """
    if not os.path.exists(DYNAMIC_FILE):
        return {}
    try:
        with open(DYNAMIC_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_dynamic_sources(data: Dict) -> None:
    os.makedirs(os.path.dirname(DYNAMIC_FILE), exist_ok=True)
    with open(DYNAMIC_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_combined_sources() -> Dict:
    """
    Combine INITIAL_SOURCES with dynamic sources (no TTL logic here).
    """
    dynamic = load_dynamic_sources()
    combined = json.loads(json.dumps(INITIAL_SOURCES))  # deep copy
    for top_key, sections in (dynamic or {}).items():
        if top_key not in combined:
            combined[top_key] = sections
            continue
        for section, data in sections.items():
            # dynamic format stores {"urls": [...], "last_updated": "..."}
            urls = data.get("urls") if isinstance(data, dict) else data
            if not isinstance(urls, list):
                continue
            if section not in combined[top_key]:
                combined[top_key][section] = urls
            else:
                combined[top_key][section] = list(dict.fromkeys(combined[top_key][section] + urls))
    return combined

def add_dynamic_sources_for_subsector(subsector_key: str, urls: List[str]) -> None:
    """
    Add URLs under dynamic['subsectors'][subsector_key] persistently with last_updated timestamp.
    """
    dynamic = load_dynamic_sources()
    if "subsectors" not in dynamic:
        dynamic["subsectors"] = {}
    existing_entry = dynamic["subsectors"].get(subsector_key, {"urls": [], "last_updated": None})
    existing_urls = existing_entry.get("urls", [])
    combined_urls = list(dict.fromkeys(existing_urls + urls))
    dynamic["subsectors"][subsector_key] = {
        "urls": combined_urls,
        "last_updated": now_iso()
    }
    save_dynamic_sources(dynamic)

def get_dynamic_subsector_entry(subsector_key: str) -> Optional[Dict]:
    dynamic = load_dynamic_sources()
    return dynamic.get("subsectors", {}).get(subsector_key)

def is_entry_expired(entry: Dict, ttl_days: int = DEFAULT_TTL_DAYS) -> bool:
    """Return True if entry is older than ttl_days."""
    if not entry or "last_updated" not in entry:
        return True
    try:
        ts = datetime.fromisoformat(entry["last_updated"])
    except Exception:
        return True
    delta = datetime.now(timezone.utc) - ts
    return delta.days >= ttl_days