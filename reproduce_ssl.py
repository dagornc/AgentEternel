from langchain_community.tools import DuckDuckGoSearchRun
import traceback

def test_ddg():
    print("Testing DuckDuckGo Search...")
    tool = DuckDuckGoSearchRun()
    try:
        result = tool.run("test query")
        print("Success!")
        print(result[:100])
    except Exception as e:
        print(f"Failed with error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_ddg()
