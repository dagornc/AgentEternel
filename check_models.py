
import requests
import json

def check_models():
    try:
        response = requests.get("https://openrouter.ai/api/v1/models")
        if response.status_code == 200:
            models = response.json().get("data", [])
            free_models = sorted([m["id"] for m in models if ":free" in m["id"]])
            
            print("--- Free Models List ---")
            for m in free_models:
                print(m)
            print("------------------------")
            
            suspicious = "openai/gpt-oss-20b:free"
            if suspicious in free_models:
                print(f"VERIFIED: Model '{suspicious}' is in the list.")
            else:
                print(f"VERIFIED: Model '{suspicious}' is NOT in the list.")
            
        else:
            print("Failed to fetch models:", response.status_code)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_models()
