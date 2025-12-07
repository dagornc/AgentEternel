"""
Defines the LangGraph workflow for the Nexus-Science agent.

This module sets up the state graph, nodes, and edges for the multi-agent research process.
"""
from langgraph.graph import StateGraph, END
from state import AgentState
from agents import RecruiterAgent, create_expert_agent, DevilsAdvocate, Synthesizer, get_alpha_evolve_expert
from tasks import recruit_task, hypothesis_task, debate_task, synthesis_task, cross_pollination_task
from crewai import Crew, Process
import json
import re
from utils import retry_llm

from crewai import Crew, Process
import asyncio

# ...

# REPO
FALLBACK_MODELS = [
    "openrouter/meta-llama/llama-3.3-70b-instruct:free",
    "openrouter/mistralai/mistral-small-3.1-24b-instruct:free",
    "openrouter/openai/gpt-oss-20b:free",
    "openrouter/google/gemma-2-9b-it:free"
]

def recruit_node(state: AgentState):
    """
    Node for recruiting experts.

    Args:
        state (AgentState): The current state of the workflow.

    Returns:
        dict: A dictionary containing the recruited 'experts' and initializing 'iterations'.
    """
    print("--- RECRUITING EXPERTS ---")
    recruiter = RecruiterAgent()
    
    experts_data = []
    
    # Determine models to try
    primary_model = state.get('model_name')
    models_to_try = [primary_model] if primary_model else []
    for m in FALLBACK_MODELS:
        if m not in models_to_try:
            models_to_try.append(m)
            
    result = None
    last_error = None

    for model in models_to_try:
        try:
            print(f"🔄 Attempting Recruit with model: {model}")
            agent = recruiter.recruit(state['input'], temperature=state.get('temperature', 0.7), model_name=model)
            task = recruit_task(agent, state['input'])
            
            # Memory disabled due to embedding API key issues
            crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)
            
            @retry_llm
            def run_crew():
                res = crew.kickoff()
                # Check if result indicates a failure (CrewAI often returns strings on failure)
                if isinstance(res, str) and ("Task Failed" in res or "Crew Execution Failed" in res or "LLM Call Failed" in res):
                     raise Exception(f"CrewAI reported failure: {res[:200]}...")
                
                # If result has direct failure output (depends on crewai version)
                if hasattr(res, 'tasks_output') and any(t.raw and "Task Failed" in t.raw for t in res.tasks_output):
                     raise Exception("CrewAI Task reported failure.")
                     
                return res
            
            result = run_crew()
            break # Success, exit loop
            
        except Exception as e:
            err_msg = str(e)
            print(f"⚠️ Model {model} failed ({err_msg}). Switching to next model...")
            last_error = e

    if result:
        # Check if result has pydantic output
        if hasattr(result, 'pydantic') and result.pydantic:
             # result.pydantic is an ExpertList instance
             for expert in result.pydantic.experts:
                 experts_data.append(expert.model_dump())
        elif hasattr(result, 'json_dict') and result.json_dict:
             if 'experts' in result.json_dict:
                 experts_data = result.json_dict['experts']
             else:
                 experts_data = result.json_dict
        else:
            # Fallback for string parsing or raw output
            print("Warning: Pydantic output not found in recruit_node.")
            # Try to parse string if it looks like JSON
            try:
                # If result is string, try to load it
                if isinstance(result, str):
                     import json
                     clean_json = result.replace("```json", "").replace("```", "")
                     data = json.loads(clean_json)
                     experts_data = data.get('experts', [])
            except:
                 pass
    
    if not experts_data:
        print(f"❌ All models failed or produced invalid output. Last error: {last_error}")
        # Fallback to default experts
        experts_data = [
            {"name": "Expert A", "role": "Generalist", "bias": "Neutral", "skill": "Problem Solving", "backstory": "Experienced generalist solver."},
            {"name": "Expert B", "role": "Specialist", "bias": "Technical", "skill": "Analysis", "backstory": "Technical specialist with deep analytical skills."},
            {"name": "Expert C", "role": "Reviewer", "bias": "Critical", "skill": "Evaluation", "backstory": "Critical reviewer focused on evaluation."}
        ]
        print("Using fallback experts due to error.")

    # ------------------------------------------------------------------
    # SYSTEMATICALLY ADD ALPHAEVOLVE EXPERT
    # ------------------------------------------------------------------
    alpha_expert = get_alpha_evolve_expert()
    # Check if not already present (based on name)
    if not any(e['name'] == alpha_expert['name'] for e in experts_data):
        print(f"Adding systematic expert: {alpha_expert['name']}")
        experts_data.append(alpha_expert)
    # ------------------------------------------------------------------

    return {"experts": experts_data, "iterations": 0}

async def hypothesis_node(state: AgentState):
    """
    Node for generating hypotheses from experts.
    PARALLELIZED.
    """
    print("--- GÉNÉRATION DES HYPOTHÈSES (PARALLEL) ---")
    experts_data = state['experts']
    
    # Determine models to try
    primary_model = state.get('model_name')
    models_to_try = [primary_model] if primary_model else []
    for m in FALLBACK_MODELS:
        if m not in models_to_try:
            models_to_try.append(m)
            
    async def run_expert(expert_data):
        for model in models_to_try:
            try:
                # Recreate agent/task inside the thread to avoid sharing state issues if any
                agent = create_expert_agent(expert_data, temperature=state.get('temperature', 0.7), web_search_enabled=state.get('web_search_enabled', True), model_name=model)
                task = hypothesis_task(agent, state['input'])
                crew = Crew(agents=[agent], tasks=[task], verbose=True)
                
                @retry_llm
                def run_crew_sync():
                    res = crew.kickoff()
                    # Check for error strings
                    if isinstance(res, str) and ("Task Failed" in res or "Crew Execution Failed" in res or "LLM Call Failed" in res):
                        raise Exception(f"CrewAI reported failure: {res[:200]}...")
                    return res
                    
                # Run blocking call in thread
                result = await asyncio.to_thread(run_crew_sync)
                return {
                    "expert_name": expert_data['name'], 
                    "role": expert_data['role'], 
                    "bias": expert_data['bias'], 
                    "hypothesis": str(result)
                }
                
            except Exception as e:
                err_msg = str(e)
                print(f"⚠️ Expert {expert_data['name']} failed with model {model} ({err_msg}). Switching to next model...")
        
        # If all failed
        print(f"❌ Expert {expert_data['name']} failed completely.")
        return {"expert_name": expert_data['name'], "hypothesis": "Error: Unable to generate hypothesis."}

    # Execute all experts in parallel
    results = await asyncio.gather(*(run_expert(e) for e in experts_data))
    
    return {"hypotheses": list(results)}

async def cross_pollination_node(state: AgentState):
    """
    Node for cross-pollination between experts.
    PARALLELIZED.
    """
    print("--- CROSS-POLLINATION (Transdisciplinarité) ---")
    hypotheses = state['hypotheses']
    experts_data = state['experts']
    
    # Map expert name to full expert data for easy lookup
    expert_map = {e['name']: e for e in experts_data}

    # Determine models to try
    primary_model = state.get('model_name')
    models_to_try = [primary_model] if primary_model else []
    for m in FALLBACK_MODELS:
        if m not in models_to_try:
            models_to_try.append(m)

    async def run_cross_pollination(h):
        expert_name = h['expert_name']
        current_hypothesis = h['hypothesis']
        
        # Get expert data
        expert_data = expert_map.get(expert_name)
        if not expert_data:
            return h
            
        # Get other hypotheses
        other_hypotheses = [oh for oh in hypotheses if oh['expert_name'] != expert_name]
        
        for model in models_to_try:
            try:
                agent = create_expert_agent(expert_data, temperature=state.get('temperature', 0.7), web_search_enabled=state.get('web_search_enabled', True), model_name=model)
                task = cross_pollination_task(agent, current_hypothesis, other_hypotheses, state['input'])
                
                # Memory disabled
                crew = Crew(agents=[agent], tasks=[task], verbose=True)
                
                @retry_llm
                def run_crew_sync():
                    res = crew.kickoff()
                    if isinstance(res, str) and ("Task Failed" in res or "Crew Execution Failed" in res or "LLM Call Failed" in res):
                         raise Exception(f"CrewAI reported failure: {res[:200]}...")
                    return res

                result = await asyncio.to_thread(run_crew_sync)
                
                return {
                    "expert_name": expert_name, 
                    "hypothesis": str(result)
                }
            except Exception as e:
                print(f"⚠️ Cross-pollination {expert_name} failed with model {model}: {e}")
                continue

        # If all failed
        print(f"❌ Cross-pollination {expert_name} failed completely.")
        return h # Keep original if error

    # Execute all cross-pollination tasks in parallel
    enriched_hypotheses = await asyncio.gather(*(run_cross_pollination(h) for h in hypotheses))

    return {"hypotheses": list(enriched_hypotheses)}

def debate_node(state: AgentState):
    """
    Node for the debate phase.
    """
    print("--- DÉBAT ---")
    
    # Determine models to try
    primary_model = state.get('model_name')
    models_to_try = [primary_model] if primary_model else []
    for m in FALLBACK_MODELS:
        if m not in models_to_try:
            models_to_try.append(m)
            
    result = "Debate skipped due to error."
    
    for model in models_to_try:
        try:
            print(f"🔄 Attempting Debate with model: {model}")
            devils_advocate = DevilsAdvocate().get_agent(temperature=state.get('temperature', 0.7), model_name=model)
            task = debate_task(devils_advocate, state['hypotheses'], state['input'])
            
            # Memory disabled
            crew = Crew(agents=[devils_advocate], tasks=[task], verbose=True)
            @retry_llm
            def run_crew():
                res = crew.kickoff()
                if isinstance(res, str) and ("Task Failed" in res or "Crew Execution Failed" in res or "LLM Call Failed" in res):
                     raise Exception(f"CrewAI reported failure: {res[:200]}...")
                return res

            result = run_crew()
            break
        except Exception as e:
            print(f"⚠️ Debate failed with model {model}: {e}")
            continue

    return {"debate_minutes": str(result)}

def synthesis_node(state: AgentState):
    """
    Node for synthesizing the final solution.
    Uses robust manual JSON parsing to avoid CrewAI recursion errors.
    """
    print("--- SYNTHESIS ---")
    
    # Determine models to try
    primary_model = state.get('model_name')
    models_to_try = [primary_model] if primary_model else []
    for m in FALLBACK_MODELS:
        if m not in models_to_try:
            models_to_try.append(m)
            
    # Append language instruction if specified
    synthesis_input = state['input']
    if state.get('language'):
        synthesis_input += f"\n\nIMPORTANT: Please write the final solution/report in {state['language']}."

    result = None
    
    for model in models_to_try:
        try:
            print(f"🔄 Attempting Synthesis with model: {model}")
            synthesizer = Synthesizer().get_agent(temperature=state.get('temperature', 0.7), model_name=model)
            task = synthesis_task(synthesizer, state['debate_minutes'], state['hypotheses'], synthesis_input)
            
            # Memory disabled
            crew = Crew(agents=[synthesizer], tasks=[task], verbose=True)
            @retry_llm
            def run_crew():
                res = crew.kickoff()
                # Check for error strings
                if isinstance(res, str) and ("Task Failed" in res or "Crew Execution Failed" in res or "LLM Call Failed" in res):
                     raise Exception(f"CrewAI reported failure: {res[:200]}...")
                return res

            result = run_crew()
            break
        except Exception as e:
            print(f"⚠️ Synthesis failed with model {model}: {e}")
            continue
            
    if result is None:
         print("❌ Synthesis failed completely.")
         return {
             "final_solution": "Synthesis failed due to technical errors.",
             "confidence_score": 0.0,
             "iterations": state['iterations'] + 1,
             "knowledge_gaps": ["Technical failure during synthesis"],
             "visualization_code": "",
             "input": state['input']
         }

    # Extract info using robust manual parsing
    solution = ""
    score = 0.0
    gaps = []
    viz_code = ""
    
    try:
        raw_output = str(result)
        
        # 1. Strip Markdown code blocks
        clean_json = raw_output.replace("```json", "").replace("```", "").strip()
        
        # 2. Sanitize Control Characters (preserve \n, \r, \t, remove others)
        # remove all chars < 32 except 9 (tab), 10 (lf), 13 (cr)
        # This regex matches control characters that are NOT \t, \n, \r
        clean_json = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', clean_json)
        
        # 3. Parse JSON
        data = json.loads(clean_json)
        
        # 4. Extract fields
        solution = data.get('solution', "")
        score = data.get('confidence_score', 0.0)
        gaps = data.get('knowledge_gaps', [])
        viz_code = data.get('visualization_code', "")
        
        # Verify types
        if not isinstance(solution, str): solution = str(solution)
        if not isinstance(score, (int, float)): score = 0.0
        if not isinstance(gaps, list): gaps = []

    except json.JSONDecodeError as e:
        print(f"⚠️ JSON Decode Error in Synthesis: {e}")
        # Attempt fallback to raw string / regex extraction if JSON fails
        solution = str(result)
        match = re.search(r'Confidence Score.*?(\d+(\.\d+)?)', solution, re.IGNORECASE)
        if match:
              score = float(match.group(1))
    except Exception as e:
        print(f"⚠️ Unexpected Error parsing synthesis: {e}")
        solution = str(result)

    # Validate score range
    if score > 1.0 and score <= 100.0:
        score = score  # Assume 0-100 scale
    elif score <= 1.0:
        score = score * 100 # Assume 0-1 scale

    # Update input with gaps if looping
    new_input = state['input']
    if score < 80 and gaps:
         gaps_text = "\n- ".join(gaps)
         if "[ITERATION UPDATE]" not in new_input:
             new_input += f"\n\n[ITERATION UPDATE] Focus on these Knowledge Gaps:\n- {gaps_text}"
         else:
             new_input += f"\n\n[NEW GAPS]:\n- {gaps_text}"

    return {
        "final_solution": solution, 
        "confidence_score": score, 
        "iterations": state['iterations'] + 1, 
        "knowledge_gaps": gaps, 
        "visualization_code": viz_code, 
        "input": new_input
    }

def check_confidence(state: AgentState):
    """
    Conditional edge to check if the confidence score is sufficient or if max iterations are reached.
    """
    target = state.get('target_confidence_score', 80.0)
    max_iter = state.get('max_iterations', 3)
    if state['confidence_score'] >= target or state['iterations'] >= max_iter:
        return "end"
    return "loop"

workflow = StateGraph(AgentState)

workflow.add_node("recruit", recruit_node)
workflow.add_node("hypothesis", hypothesis_node)
workflow.add_node("cross_pollination", cross_pollination_node)
workflow.add_node("debate", debate_node)
workflow.add_node("synthesis", synthesis_node)

workflow.set_entry_point("recruit")
workflow.add_edge("recruit", "hypothesis")
workflow.add_edge("hypothesis", "cross_pollination")
workflow.add_edge("cross_pollination", "debate")
workflow.add_edge("debate", "synthesis")

workflow.add_conditional_edges(
    "synthesis",
    check_confidence,
    {
        "end": END,
        "loop": "hypothesis"
    }
)

app = workflow.compile()
