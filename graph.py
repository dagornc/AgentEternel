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
FALLBACK_MODEL = "openrouter/meta-llama/llama-3.3-70b-instruct:free"

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
    agent = recruiter.recruit(state['input'], temperature=state.get('temperature', 0.7), model_name=state.get('model_name'))
    task = recruit_task(agent, state['input'])
    
    # Memory disabled due to embedding API key issues
    crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)
    @retry_llm
    def run_crew():
        return crew.kickoff()
    
    experts_data = []

    try:
        try:
            result = run_crew()
        except Exception as e:
            err_msg = str(e)
            print(f"⚠️ Primary model failed ({err_msg}). Retrying with FALLBACK_MODEL...")
            # Fallback attempt
            agent = recruiter.recruit(state['input'], temperature=state.get('temperature', 0.7), model_name=FALLBACK_MODEL)
            task = recruit_task(agent, state['input'])
            crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)
            result = crew.kickoff()

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
                raise ValueError("No structured output returned")

    except Exception as e:
        print(f"❌ ERROR in recruit_node: {e}")
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

def hypothesis_node(state: AgentState):
    """
    Node for generating hypotheses from experts.
    PARALLELIZED.
    """
    print("--- GÉNÉRATION DES HYPOTHÈSES ---")
    experts_data = state['experts']
    hypotheses = []
    
    # Sequential execution for stability
    for expert_data in experts_data:
        try:
            agent = create_expert_agent(expert_data, temperature=state.get('temperature', 0.7), web_search_enabled=state.get('web_search_enabled', True), model_name=state.get('model_name'))
            task = hypothesis_task(agent, state['input'])
            # Memory disabled
            crew = Crew(agents=[agent], tasks=[task], verbose=True) 
            @retry_llm
            def run_crew():
                return crew.kickoff()
                
            try:
                result = run_crew()
                hypotheses.append({"expert_name": expert_data['name'], "hypothesis": str(result)})
            except Exception as e:
                err_msg = str(e)
                print(f"⚠️ Expert {expert_data['name']} failed ({err_msg}). Retrying with FALLBACK_MODEL...")
                try:
                    agent = create_expert_agent(expert_data, temperature=state.get('temperature', 0.7), web_search_enabled=state.get('web_search_enabled', True), model_name=FALLBACK_MODEL)
                    task = hypothesis_task(agent, state['input'])
                    crew = Crew(agents=[agent], tasks=[task], verbose=True)
                    result = crew.kickoff()
                    hypotheses.append({"expert_name": expert_data['name'], "hypothesis": str(result)})
                except Exception as e2:
                    print(f"❌ Expert {expert_data['name']} failed completely: {e2}")
                    hypotheses.append({"expert_name": expert_data['name'], "hypothesis": "Error: Unable to generate hypothesis."})

        except Exception as e:
            print(f"Error executing expert {expert_data['name']}: {e}")
            hypotheses.append({"expert_name": expert_data['name'], "hypothesis": f"Error: {e}"})

    return {"hypotheses": hypotheses}

def cross_pollination_node(state: AgentState):
    """
    Node for cross-pollination between experts.
    """
    print("--- CROSS-POLLINATION (Transdisciplinarité) ---")
    hypotheses = state['hypotheses']
    experts_data = state['experts']
    
    enriched_hypotheses = []
    
    # Map expert name to full expert data for easy lookup
    expert_map = {e['name']: e for e in experts_data}

    for h in hypotheses:
        expert_name = h['expert_name']
        current_hypothesis = h['hypothesis']
        
        # Get expert data
        expert_data = expert_map.get(expert_name)
        if not expert_data:
            continue
            
        # Get other hypotheses
        other_hypotheses = [oh for oh in hypotheses if oh['expert_name'] != expert_name]
        
        try:
            agent = create_expert_agent(expert_data, temperature=state.get('temperature', 0.7), web_search_enabled=state.get('web_search_enabled', True), model_name=state.get('model_name'))
            task = cross_pollination_task(agent, current_hypothesis, other_hypotheses, state['input'])
            
            # Memory disabled
            crew = Crew(agents=[agent], tasks=[task], verbose=True)
            @retry_llm
            def run_crew():
                return crew.kickoff()

            try:
                result = run_crew()
            except Exception as e:
                err_msg = str(e)
                print(f"⚠️ Cross-pollination {expert_name} failed ({err_msg}). Retrying with FALLBACK_MODEL...")
                try:
                    agent = create_expert_agent(expert_data, temperature=state.get('temperature', 0.7), web_search_enabled=state.get('web_search_enabled', True), model_name=FALLBACK_MODEL)
                    task = cross_pollination_task(agent, current_hypothesis, other_hypotheses, state['input'])
                    crew = Crew(agents=[agent], tasks=[task], verbose=True)
                    result = crew.kickoff()
                except Exception as e2:
                    print(f"❌ Cross-pollination {expert_name} failed completely: {e2}")
                    result = current_hypothesis # Fallback to original

            
            enriched_hypotheses.append({
                "expert_name": expert_name, 
                "hypothesis": str(result) # Replaces the old hypothesis with the enriched one
            })
        except Exception as e:
             print(f"Error in cross-pollination for {expert_name}: {e}")
             enriched_hypotheses.append(h) # Keep original if error

    return {"hypotheses": enriched_hypotheses}

def debate_node(state: AgentState):
    """
    Node for the debate phase.
    """
    print("--- DÉBAT ---")
    devils_advocate = DevilsAdvocate().get_agent(temperature=state.get('temperature', 0.7), model_name=state.get('model_name'))
    task = debate_task(devils_advocate, state['hypotheses'], state['input'])
    
    # Memory disabled
    crew = Crew(agents=[devils_advocate], tasks=[task], verbose=True)
    @retry_llm
    def run_crew():
        return crew.kickoff()

    try:
        result = run_crew()
    except Exception as e:
        err_msg = str(e)
        print(f"⚠️ Debate failed ({err_msg}). Retrying with FALLBACK_MODEL...")
        try:
             devils_advocate = DevilsAdvocate().get_agent(temperature=state.get('temperature', 0.7), model_name=FALLBACK_MODEL)
             task = debate_task(devils_advocate, state['hypotheses'], state['input'])
             crew = Crew(agents=[devils_advocate], tasks=[task], verbose=True)
             result = crew.kickoff()
        except Exception as e2:
             print(f"❌ Debate failed completely: {e2}")
             result = "Debate skipped due to error."
    return {"debate_minutes": str(result)}

def synthesis_node(state: AgentState):
    """
    Node for synthesizing the final solution.
    Uses Pydantic structured output.
    """
    print("--- SYNTHESIS ---")
    synthesizer = Synthesizer().get_agent(temperature=state.get('temperature', 0.7), model_name=state.get('model_name'))
    
    # Append language instruction if specified
    synthesis_input = state['input']
    if state.get('language'):
        synthesis_input += f"\n\nIMPORTANT: Please write the final solution/report in {state['language']}."

    task = synthesis_task(synthesizer, state['debate_minutes'], state['hypotheses'], synthesis_input)
    
    # Memory disabled
    crew = Crew(agents=[synthesizer], tasks=[task], verbose=True)
    @retry_llm
    def run_crew():
        return crew.kickoff()

    try:
        result = run_crew()
    except Exception as e:
        err_msg = str(e)
        print(f"⚠️ Synthesis failed ({err_msg}). Retrying with FALLBACK_MODEL...")
        try:
             synthesizer = Synthesizer().get_agent(temperature=state.get('temperature', 0.7), model_name=FALLBACK_MODEL)
             task = synthesis_task(synthesizer, state['debate_minutes'], state['hypotheses'], synthesis_input)
             crew = Crew(agents=[synthesizer], tasks=[task], verbose=True)
             result = crew.kickoff()
        except Exception as e2:
             print(f"❌ Synthesis failed completely: {e2}")
             result = "Synthesis skipped due to error. Please check individual hypotheses."
    
    # Extract confidence score from Pydantic output
    solution = ""
    score = 0.0
    
    try:
        if hasattr(result, 'pydantic') and result.pydantic:
            solution = result.pydantic.solution
            score = result.pydantic.confidence_score
            gaps = getattr(result.pydantic, 'knowledge_gaps', [])
            viz_code = getattr(result.pydantic, 'visualization_code', "")
        elif hasattr(result, 'json_dict') and result.json_dict:
            solution = result.json_dict.get('solution', str(result))
            score = result.json_dict.get('confidence_score', 0.0)
            gaps = result.json_dict.get('knowledge_gaps', [])
            viz_code = result.json_dict.get('visualization_code', "")
        else:
             # Fallback
             solution = str(result)
             match = re.search(r'Confidence Score.*?(\d+(\.\d+)?)', solution, re.IGNORECASE)
             if match:
                  score = float(match.group(1))
             gaps = []
             viz_code = ""
    except Exception as e:
        print(f"Error parsing synthesis: {e}")
        solution = str(result)
        gaps = []
        viz_code = ""
        
    # Update input with gaps if looping
    new_input = state['input']
    if score < 80 and gaps:
         gaps_text = "\n- ".join(gaps)
         # Check if we already appended to avoid duplication
         if "[ITERATION UPDATE]" not in new_input:
             new_input += f"\n\n[ITERATION UPDATE] Focus on these Knowledge Gaps:\n- {gaps_text}"
         else:
             # Basic append for now, or replace logic if feeling fancy. 
             # Let's just append new gaps.
             new_input += f"\n\n[NEW GAPS]:\n- {gaps_text}"

    return {"final_solution": solution, "confidence_score": score, "iterations": state['iterations'] + 1, "knowledge_gaps": gaps, "visualization_code": viz_code, "input": new_input}

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
