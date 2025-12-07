from duckduckgo_search import DDGS
import traceback

def verify_direct():
    print("Verifying DuckDuckGo Search (Direct DDGS)...")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text("test run", max_results=1))
            if results:
                print("Success! Found results.")
                print(results[0])
            else:
                print("Success! No results found, but no error.")
    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    verify_direct()
