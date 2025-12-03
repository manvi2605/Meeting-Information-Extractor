# list_models.py
import os, requests, json
api_key = os.environ.get("GEMINI_API_KEY", "AIzaSyDBBDvgLh40lcqe2TxTCVqRFnWOimBYal0")
for version in ("v1/models", "v1beta/models", "v1beta2/models"):
    url = f"https://generativelanguage.googleapis.com/{version}?key={api_key}"
    print("QUERY:", url)
    r = requests.get(url, timeout=10)
    print("STATUS", r.status_code)
    try:
        j = r.json()
        print(json.dumps(j, indent=2)[:2000])
    except Exception:
        print(r.text[:2000])
    print("="*80)
