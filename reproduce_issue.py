
import os
os.environ["OPENAI_API_KEY"] = "sk-dummy-key" # Mock key for CrewAI initialization
from crewai import Agent, Task, Crew, Process
from unittest.mock import MagicMock
import litellm

# Mock LLM that raises RateLimitError
def mock_llm_call(*args, **kwargs):
    raise litellm.RateLimitError("Rate limit exceeded", llm_provider="openrouter", model="test")

# Create a dummy agent with a failing LLM
agent = Agent(
    role='Test Agent',
    goal='Fail',
    backstory='I am designed to fail.',
    verbose=True,
    allow_delegation=False
)

# Monkey patch the llm call to fail
# Note: This is tricky because CrewAI wraps LLMs. 
# Better to rely on the behavior observed: exception propagates from our retry_llm decorator.

from utils import retry_llm

@retry_llm
def failing_function():
    print("Calling failing function...")
    raise litellm.RateLimitError("Rate limit exceeded", llm_provider="openrouter", model="test")

# Test 1: Does retry_llm propagate the exception?
try:
    failing_function()
except Exception as e:
    print(f"Caught expected exception from failing_function: {type(e).__name__}")

# Test 2: CrewAI context
# We need to see if crew.kickoff() catches this if it happens inside an agent's execution.
# Since we can't easily mock the internal LLM call of CrewAI without complex patching, 
# let's assume the user's log is truth: "LLM Call Failed" and then "Task Failed".

# If retry_llm is wrapping crew.kickoff(), then it SHOULD propagate.
# In graph.py:
# @retry_llm
# def run_crew():
#     return crew.kickoff()

# So if crew.kickoff() raises, run_crew raises.
# BUT, if crew.kickoff() catches the LLM error internally and just returns a "failed" output string,
# then run_crew will NOT raise, and fallback won't trigger.

print("\n--- Simulation ---")

class MockCrew:
    def kickoff(self):
        print("MockCrew.kickoff running...")
        # Simulate CrewAI behavior: it likely catches LLM errors to prevent full crash?
        # OR it re-raises them? 
        # The user log shows "LLM Error" then "Task Failure" then "Crew Execution Failed".
        # This usually implies CrewAI caught it and logged it.
        
        # If I look at the user log: 
        # ❌ Crew: crew
        # ...
        # Status: ❌ Failed
        # └── ❌ LLM Failed
        
        # This strongly suggests kickoff returns, it does NOT raise.
        return "Error: Task failed due to LLM error." 

# Verify our assumption about graph.py logic
@retry_llm
def run_crew_simulated():
    crew = MockCrew()
    return crew.kickoff()

try:
    result = run_crew_simulated()
    print(f"Result from run_crew_simulated: {result}")
    
    # This is the problem! If result is returned, the outer try-except in graph.py 
    # (which expects an exception) does NOTHING.
    
    if "Error" in str(result) or "Failed" in str(result):
        raise Exception("Detected failure in result string")
        
except Exception as e:
    print(f"Caught exception in outer block: {e}")
