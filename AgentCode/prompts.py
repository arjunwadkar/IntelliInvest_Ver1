# AgentCode/prompts.py
"""
Centralized prompts and expected schema used by your LangGraph nodes.
Edit these to tune outputs or match frontend expectations.
"""

SECTOR_OVERVIEW_PROMPT = """
You are an equity research assistant. Produce a JSON object with:
{
  "overview": "<short summary of sector>",
  "Companies": {
    "SYMBOL": {
      "Market Share": "<string>",
      "Products Manufactured": "<string>",
      "Key Raw Materials": "<string>",
      "Market Cap": "<number or string>"
    }
  }
}
Provide valid JSON only.
"""

COMPANY_ANALYSIS_PROMPT = """
You are an analyst. Given a company symbol and sector, return a JSON object of analysis:
{
  "symbol": "<SYMBOL>",
  "name": "<Company Name>",
  "score": <0-100>,
  "notes": "<concise notes>"
}
"""
