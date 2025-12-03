import os
from fastapi import FastAPI
from pydantic import BaseModel
from meeting_extractor.llm_client import extract_action_items
from datetime import datetime

app = FastAPI()

class ExtractRequest(BaseModel):
    transcript: str
    meeting_id: str | None = None
    format: str = "json"  # Options: "json", "markdown", "detailed"

def format_as_markdown(result: dict) -> str:
    """Format action items as markdown."""
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
    """Format action items with enhanced details."""
    return {
        "metadata": {
            "meeting_id": result.get("meeting_id", "N/A"),
            "total_items": len(result.get("action_items", [])),
            "generated_at": datetime.now().isoformat(),
            "high_priority_count": sum(1 for item in result.get("action_items", []) 
                                       if item.get("priority", "").lower() in ["high", "urgent"])
        },
        "action_items": [
            {
                "id": item.get("id"),
                "task": item.get("text"),
                "assignee": item.get("possible_owner"),
                "deadline": item.get("suggested_due"),
                "priority_level": item.get("priority", "Normal"),
                "confidence_score": f"{item.get('confidence', 0.0):.0%}",
                "evidence": item.get("evidence", [])
            }
            for item in result.get("action_items", [])
        ]
    }

def format_as_pretty(result: dict) -> str:
    """Format action items as clean readable text with line breaks."""
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

@app.post("/extract")
def extract(req: ExtractRequest):
    try:
        meeting_id = req.meeting_id or "meeting_1"
        result = extract_action_items(req.transcript, meeting_id)
        
        # Apply formatting based on request
        if req.format == "markdown":
            return {"formatted": format_as_markdown(result), "raw": result}
        elif req.format == "detailed":
            return format_as_detailed(result)
        elif req.format == "pretty":
            return {"formatted": format_as_pretty(result)}
        else:  # Default JSON
            return result
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e), "type": type(e).__name__}
