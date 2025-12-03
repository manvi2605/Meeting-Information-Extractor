# server/main.py
import os
import logging
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

# Import your extraction function
from meeting_extractor.llm_client import extract_action_items

# --- Setup logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("meeting_extractor")

# --- FastAPI app ---
app = FastAPI(title="Meeting Extractor", version="1.0")

# --- Health / root route ---
@app.get("/")
async def home():
    return {"status": "ok", "message": "Meeting Extractor API is running!"}


# --- Request model ---
class ExtractRequest(BaseModel):
    transcript: str
    meeting_id: Optional[str] = None
    format: str = "json"  # Options: "json", "markdown", "detailed", "pretty"


# --- Formatting helpers (your code, lightly refactored) ---
def format_as_markdown(result: dict) -> str:
    md = f"# Meeting Action Items\n\n"
    md += f"**Meeting ID:** {result.get('meeting_id', 'N/A')}\n"
    md += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    md += "---\n\n"

    for item in result.get("action_items", []):
        md += f"## {item.get('id', 'N/A')} - {item.get('text', 'N/A')}\n\n"
        md += f"- **Owner:** {item.get('possible_owner', 'TBD')}\n"
        md += f"- **Due Date:** {item.get('suggested_due', 'Not specified')}\n"
        md += f"- **Priority:** {item.get('priority', 'N/A')}\n"
        md += f"- **Confidence:** {item.get('confidence', 0.0):.0%}\n\n"

    return md


def format_as_detailed(result: dict) -> dict:
    return {
        "metadata": {
            "meeting_id": result.get("meeting_id", "N/A"),
            "total_items": len(result.get("action_items", [])),
            "generated_at": datetime.now().isoformat(),
            "high_priority_count": sum(
                1
                for item in result.get("action_items", [])
                if item.get("priority", "").lower() in ["high", "urgent"]
            ),
        },
        "action_items": [
            {
                "id": item.get("id"),
                "task": item.get("text"),
                "assignee": item.get("possible_owner"),
                "deadline": item.get("suggested_due"),
                "priority_level": item.get("priority", "Normal"),
                "confidence_score": f"{item.get('confidence', 0.0):.0%}",
                "evidence": item.get("evidence", []),
            }
            for item in result.get("action_items", [])
        ],
    }


def format_as_pretty(result: dict) -> str:
    lines = []
    lines.append("=" * 70)
    lines.append("MEETING ACTION ITEMS REPORT")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"Meeting ID: {result.get('meeting_id', 'N/A')}")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Total Items: {len(result.get('action_items', []))}")
    lines.append("")
    lines.append("=" * 70)
    lines.append("")

    for idx, item in enumerate(result.get("action_items", []), 1):
        lines.append(f"TASK #{idx}")
        lines.append("-" * 70)
        lines.append("")
        lines.append(f"  ID:              {item.get('id', 'N/A')}")
        lines.append("")
        lines.append(f"  Task:            {item.get('text', 'N/A')}")
        lines.append("")
        lines.append(f"  Assignee:        {item.get('possible_owner', 'TBD')}")
        lines.append("")
        lines.append(f"  Due Date:        {item.get('suggested_due', 'Not specified')}")
        lines.append("")
        lines.append(f"  Priority:        {item.get('priority', 'N/A')}")
        lines.append("")
        lines.append(f"  Confidence:      {item.get('confidence', 0.0):.0%}")
        lines.append("")
        if item.get("evidence"):
            lines.append(f"  Evidence:        {', '.join(item.get('evidence', []))}")
            lines.append("")
        lines.append("")

    lines.append("=" * 70)
    return "\n".join(lines)


# --- /extract endpoint (non-blocking) ---
@app.post("/extract")
async def extract(req: ExtractRequest):
    """
    Accepts a meeting transcript and returns extracted action items.
    This endpoint runs extract_action_items in a threadpool to avoid
    blocking the ASGI event loop if the extraction function is synchronous.
    """
    meeting_id = req.meeting_id or f"meeting_{int(datetime.now().timestamp())}"
    logger.info("Received extract request for meeting_id=%s format=%s", meeting_id, req.format)

    try:
        # Run extraction in a thread if the function is synchronous
        result = await run_in_threadpool(extract_action_items, req.transcript, meeting_id)

        # Ensure result is a dict and includes meeting_id
        if not isinstance(result, dict):
            logger.warning("extract_action_items returned non-dict type: %s", type(result))
            raise ValueError("Extraction function did not return a dict")

        result.setdefault("meeting_id", meeting_id)
        result.setdefault("action_items", result.get("action_items", []))

        # Formatting selection
        fmt = req.format.lower() if req.format else "json"
        if fmt == "markdown":
            formatted = format_as_markdown(result)
            return {"success": True, "format": "markdown", "formatted": formatted, "raw": result}
        elif fmt == "detailed":
            detailed = format_as_detailed(result)
            return {"success": True, "format": "detailed", "result": detailed}
        elif fmt == "pretty":
            pretty = format_as_pretty(result)
            return {"success": True, "format": "pretty", "formatted": pretty}
        else:  # default JSON
            return {"success": True, "format": "json", "result": result}

    except Exception as exc:
        logger.exception("Error during extraction: %s", exc)
        # Return safe error info; avoid leaking secrets
        raise HTTPException(status_code=500, detail=str(exc))


# --- Local dev runner (ignored by Render; Render uses uvicorn with --port $PORT) ---
if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    logger.info("Starting local dev server on port %s", port)
    uvicorn.run("server.main:app", host="0.0.0.0", port=port, reload=True)
