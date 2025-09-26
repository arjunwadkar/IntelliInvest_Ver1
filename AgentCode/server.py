# server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from research_agent import app as langgraph_app

# FastAPI + models
class AnalyzeRequest(BaseModel):
    sector: str

class SubsectorRequest(BaseModel):
    subsector: str

app = FastAPI()
# allow requests from frontend dev server (adjust origin for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/analyze")
async def analyze(req: AnalyzeRequest):
    if not req.sector:
        raise HTTPException(status_code=400, detail="sector required")
    # invoke langgraph graph
    state = langgraph_app.invoke({"user_message": req.sector})
    # state contains assistant_response and stage
    return {
        "assistant_response": state.get("assistant_response"),
        "stage": state.get("stage")
    }

@app.post("/api/subsector")
async def subsector(req: SubsectorRequest):
    if not req.subsector:
        raise HTTPException(status_code=400, detail="subsector required")
    state = langgraph_app.invoke({"user_message": req.subsector, "stage": "subsector_detail"})
    return {
        "assistant_response": state.get("assistant_response"),
        "stage": state.get("stage")
    }

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)