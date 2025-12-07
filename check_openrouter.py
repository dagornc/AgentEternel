
import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("OPENROUTER_API_KEY")
print(f"Checking OpenRouter API Key...")
if not api_key:
    print("❌ OPENROUTER_API_KEY not found in environment.")
else:
    print(f"✅ OPENROUTER_API_KEY found: {api_key[:5]}...{api_key[-4:]}")

print("\nTesting Model Availability...")

def get_openrouter_free_models():
    try:
        response = requests.get("https://openrouter.ai/api/v1/models")
        if response.status_code == 200:
            models = response.json()["data"]
            free_models = [m["id"] for m in models if ":free" in m["id"]]
            return sorted(free_models)
        else:
            print(f"❌ API Error: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"❌ Exception fetching models: {e}")
        return []

free_models = get_openrouter_free_models()
if free_models:
    print(f"✅ Found {len(free_models)} free models:")
    for m in free_models:
        print(f"  - {m}")
else:
    print("⚠️ No free models found or API failed.")

print("\nVerifying LiteLLM Configuration in agents.py...")
# We will do a simple static check of the file content here or just inspect it manually.
# But let's try a dry run of an agent creation if possible.
try:
    from agents import get_llm
    llm = get_llm()
    print(f"✅ get_llm() returned successfully. Model: {llm.model}")
    if "openrouter/" in llm.model:
        print("✅ Model has 'openrouter/' prefix.")
    else:
        print("⚠️ Model MISSING 'openrouter/' prefix.")
except Exception as e:
    print(f"❌ Error initializing LLM: {e}")
