# AgentCode/sources.py
"""
Excel export helpers; can be used by server or invoked standalone.
This file uses openpyxl only if you want server-side xlsx generation.
The current server returns JSON and client turns it into Excel with SheetJS.
"""
from openpyxl import Workbook
from io import BytesIO

def rows_to_xlsx_bytes(rows):
    wb = Workbook()
    ws = wb.active
    if not rows:
        ws.append(["No data"])
    else:
        headers = list(rows[0].keys())
        ws.append(headers)
        for r in rows:
            ws.append([r.get(h, "") for h in headers])
    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)
    return bio.read()
