# meeting_extractor/utils.py
import re
from typing import List, Dict

def simple_speaker_split(transcript: str):
    """
    Very small heuristic parser for transcripts formatted as 'Speaker: text'
    Returns list of utterances: [{speaker, time, text}]
    """
    lines = transcript.splitlines()
    utterances = []
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        # try to parse "HH:MM Speaker: text" or "Speaker: text"
        m = re.match(r'^(?:(\d{1,2}:\d{2})\s+)?([^:]+):\s*(.+)$', ln)
        if m:
            time = m.group(1) or ""
            speaker = m.group(2).strip()
            text = m.group(3).strip()
        else:
            # fallback: unknown speaker
            time = ""
            speaker = "Unknown"
            text = ln
        utterances.append({"speaker": speaker, "time": time, "text": text})
    return {"utterances": utterances}
