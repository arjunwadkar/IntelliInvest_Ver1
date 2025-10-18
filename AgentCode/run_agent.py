# AgentCode/run_agent.py
"""
Small CLI to test run_analysis locally.
Usage: python run_agent.py --mode=stub --sector="Automobiles" --subsector="Tyres"
"""
import argparse
import json
from .research_agent import run_analysis

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument('--mode', default='stub')
    p.add_argument('--sector', default='Automobiles')
    p.add_argument('--subsector', default='')
    p.add_argument('--prompt', default='')
    args = p.parse_args()
    out = run_analysis(mode=args.mode, sector=args.sector, subsector=args.subsector, prompt=args.prompt, use_cache=False)
    print(json.dumps(out, indent=2))
