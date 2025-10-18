# AgentCode/server.py
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import json
import os
from typing import Optional, List, Dict
from datetime import datetime
from pathlib import Path

# Import run_analysis wrapper from research_agent
from .research_agent import run_analysis

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"
DB_PATH = str(BASE_DIR / "equity_research.db")

app = FastAPI(title="Equity Research API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# ============ DB helpers ============
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS cache (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mode TEXT,
        sector TEXT,
        subsector TEXT,
        prompt TEXT,
        response TEXT,
        created_at TEXT
    )''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS sectors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sector TEXT,
        subsector TEXT
    )''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT,
        name TEXT,
        sector TEXT,
        subsector TEXT,
        market_cap REAL,
        last_updated TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

# ============ config loader ============
def load_config():
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
        except Exception:
            return {}
    return {}

# ============ simple cache wrapper ============
def cached_response(mode, sector, subsector, prompt=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT response FROM cache WHERE mode=? AND sector=? AND subsector=? ORDER BY id DESC LIMIT 1', (mode, sector, subsector))
    row = cur.fetchone()
    conn.close()
    return json.loads(row['response']) if row else None

def cache_insert(mode, sector, subsector, prompt, response):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('INSERT INTO cache (mode, sector, subsector, prompt, response, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                (mode, sector, subsector, prompt or '', json.dumps(response), datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

# ============ API models ============
class AnalyzeRequest(BaseModel):
    sector: str
    subsector: Optional[str] = ''
    mode: Optional[str] = None
    prompt: Optional[str] = None
    force: Optional[bool] = False

# ============ endpoints ============
@app.get('/sectors')
def get_sectors():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT DISTINCT sector FROM sectors ORDER BY sector')
    sectors = [r['sector'] for r in cur.fetchall()]
    result = {}
    for s in sectors:
        cur.execute('SELECT subsector FROM sectors WHERE sector=? ORDER BY subsector', (s,))
        subs = [r['subsector'] for r in cur.fetchall()]
        result[s] = subs
    conn.close()
    return result

@app.get('/companies')
def get_companies(sector: str = Query(...), subsector: Optional[str] = Query(None)):
    conn = get_conn()
    cur = conn.cursor()
    if subsector:
        cur.execute('SELECT * FROM companies WHERE sector=? AND subsector=? ORDER BY name', (sector, subsector))
    else:
        cur.execute('SELECT * FROM companies WHERE sector=? ORDER BY name', (sector,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

@app.post('/analyze')
def analyze(req: AnalyzeRequest):
    mode = (req.mode or load_config().get('mode') or 'stub').lower()
    if not req.force:
        cached = cached_response(mode, req.sector, req.subsector or '', req.prompt)
        if cached:
            return {'from_cache': True, 'result': cached}
    # call the wrapper
    result = run_analysis(mode=mode, sector=req.sector, subsector=req.subsector, prompt=req.prompt)
    cache_insert(mode, req.sector, req.subsector or '', req.prompt, result)
    return {'from_cache': False, 'result': result}

@app.get('/export')
def export_companies(sector: str = Query(...), subsector: Optional[str] = Query(None)):
    conn = get_conn()
    cur = conn.cursor()
    if subsector:
        cur.execute('SELECT symbol, name, sector, subsector, market_cap FROM companies WHERE sector=? AND subsector=?', (sector, subsector))
    else:
        cur.execute('SELECT symbol, name, sector, subsector, market_cap FROM companies WHERE sector=?', (sector,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {'rows': rows}

@app.post('/admin/seed')
def admin_seed(items: Dict[str, List[str]]):
    conn = get_conn()
    cur = conn.cursor()
    for s, subs in items.items():
        for sub in subs:
            cur.execute('SELECT 1 FROM sectors WHERE sector=? AND subsector=?', (s, sub))
            if not cur.fetchone():
                cur.execute('INSERT INTO sectors (sector, subsector) VALUES (?, ?)', (s, sub))
    conn.commit()
    conn.close()
    return {'seeded': True}

# Placeholder endpoint for market refresh - implement provider-specific logic
@app.post('/refresh-market-data')
def refresh_market_data(api_provider: str = 'twelvedata'):
    config = load_config()
    apikey = os.environ.get('MARKET_API_KEY') or config.get('market_api_key')
    if not apikey:
        return {'updated': 0, 'note': 'No API key configured or running in stub mode.'}
    # TODO: Implement TwelveData / FMP calls; batch symbols, update companies table
    return {'updated': 0, 'note': 'Market refresh not implemented in scaffold.'}
