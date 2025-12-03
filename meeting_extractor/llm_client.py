import os
import requests
import json
import re
from dotenv import load_dotenv

load_dotenv(override=True)

API_KEY = os.getenv("GEMINI_API_KEY")


def extract_action_items(transcript: str, meeting_id: str = "meeting_1"):
    """
    Calls Google Gemini API to extract action items from transcript.
    """
    
    # Load environment variables fresh
    load_dotenv(override=True)
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise Exception("GEMINI_API_KEY is not set in environment (.env). Set GEMINI_API_KEY before calling the API.")
    
    model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    api_version = os.getenv("GEMINI_API_VERSION", "v1beta")
    
    gemini_url = f"https://generativelanguage.googleapis.com/{api_version}/models/{model}:generateContent"

    prompt = f"""
    Extract all action items from this meeting transcript. 
    Return ONLY a JSON list of action items (no explanation):

    Transcript:
    {transcript}

    JSON Format:
    {{
        "meeting_id": "{meeting_id}",
        "action_items": [
            {{
                "id": "A1",
                "text": "",
                "possible_owner": "",
                "suggested_due": "",
                "priority": "",
                "evidence": [],
                "confidence": 0.0
            }}
        ]
    }}
    """

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": api_key
    }

    response = requests.post(gemini_url, headers=headers, data=json.dumps(payload), timeout=30)

    if response.status_code != 200:
        raise Exception(f"Gemini API Error {response.status_code}: {response.text}")

    data = response.json()

    # Extract model text safely
    result_text = data["candidates"][0]["content"]["parts"][0]["text"]

    # Remove markdown code blocks if present
    if isinstance(result_text, str):
        if result_text.strip().startswith("```json"):
            result_text = result_text.strip()[7:]
        if result_text.strip().startswith("```"):
            result_text = result_text.strip()[3:]
        if result_text.strip().endswith("```"):
            result_text = result_text.strip()[:-3]
    
    result_text = result_text.strip()

    # Convert string JSON → Python dict
    try:
        result_json = json.loads(result_text)
        return result_json
    except json.JSONDecodeError:
        # Fallback: attempt to extract JSON substring
        m = re.search(r"(\{[\s\S]*\})", result_text)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                pass
        raise Exception(f"Model returned invalid JSON:\n{result_text}")