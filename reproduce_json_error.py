import json
import re

def test_json_sanitization():
    # Simulate invalid JSON with control characters (e.g. \x00, \x1F) and markdown blocks
    raw_output = "```json\n{\n  \"solution\": \"Test Solution\\n with invalid char \x1F\",\n  \"confidence_score\": 95,\n  \"knowledge_gaps\": [],\n  \"visualization_code\": \"graph TD; A-->B\"\n}\n```"
    
    print(f"Original Raw Output: {repr(raw_output)}")

    # 1. Strip Markdown code blocks
    clean_json = raw_output.replace("```json", "").replace("```", "").strip()
    
    # 2. Sanitize Control Characters (preserve \n, \r, \t, remove others)
    # This regex matches control characters that are NOT \t, \n, \r
    clean_json = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', clean_json)
    
    print(f"Sanitized JSON: {repr(clean_json)}")

    try:
        # 3. Parse JSON
        data = json.loads(clean_json)
        print("✅ JSON parsed successfully!")
        print("Parsed Data:", data)
        return True
    except json.JSONDecodeError as e:
        print(f"❌ JSON Decode Error: {e}")
        return False

if __name__ == "__main__":
    if test_json_sanitization():
        print("Test PASSED")
    else:
        print("Test FAILED")
