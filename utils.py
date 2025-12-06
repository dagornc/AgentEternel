
import time
from functools import wraps

def format_output(final_state):
    """
    Formats the final state of the workflow into a Markdown report.

    Args:
        final_state (dict): The final state dictionary from the workflow.

    Returns:
        str: A formatted Markdown string containing the report.
    """
    output = "# Rapport de Recherche Nexus-Science\n\n"
    
    # 1. Panel of Experts
    output += "## 1. Panel d'Experts\n\n"
    output += "| Nom | Rôle | Biais | Compétence Signature |\n"
    output += "|---|---|---|---|\n"
    if 'experts' in final_state:
        for expert in final_state['experts']:
            output += f"| {expert['name']} | {expert['role']} | {expert['bias']} | {expert['skill']} |\n"
    output += "\n"
    
    # 2. Debate Minutes
    output += "## 2. Minutes du Débat\n\n"
    if 'debate_minutes' in final_state:
        output += final_state['debate_minutes'] + "\n\n"
    
    # 3. Final Solution
    output += "## 3. Solution Finale & Limites\n\n"
    if 'final_solution' in final_state:
        output += final_state['final_solution'] + "\n"
    


    # 4. Visualization
    output += "\n## 4. Carte Transdisciplinaire (Concepts)\n\n"
    if 'visualization_code' in final_state and final_state['visualization_code']:
        output += "```mermaid\n"
        output += final_state['visualization_code']
        output += "\n```\n"

    return output

def retry_llm(func):
    """
    Decorator to retry a function call upon failure.
    Retries 3 times with a 2-second delay.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        retries = 3
        delay = 2
        last_exception = None
        for i in range(retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                # Don't sleep on the last attempt
                if i < retries - 1:
                    time.sleep(delay)
        raise last_exception
    return wrapper
