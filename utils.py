
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

import litellm
import random

def retry_llm(func):
    """
    Decorator to retry a function call upon failure.
    Retries with exponential backoff, specifically handling RateLimitErrors.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        max_retries = 9  # High retry count for rate limits
        base_delay = 10   # Start with 10 seconds for rate limits
        
        for i in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Check for RateLimitError (either class or string 429)
                is_rate_limit = isinstance(e, litellm.RateLimitError) or "429" in str(e) or "RateLimitError" in str(e)
                
                if i < max_retries - 1:
                    if is_rate_limit:
                        # Exponential backoff for rate limits: 10, 20, 40, 80... capped at 120s
                        delay = min(120, (base_delay * (2 ** i)) + random.uniform(1, 5))
                        print(f"⏳ Quota dépassé (Rate Limit). Attente de {delay:.1f}s avant nouvelle tentative {i+1}/{max_retries}...")
                    else:
                        # Standard backoff for other errors
                        delay = min(60, (2 * (2 ** i)) + random.uniform(0, 1))
                        print(f"⚠️ Erreur ({e}). Nouvelle tentative dans {delay:.1f}s... ({i+1}/{max_retries})")
                    
                    time.sleep(delay)
                else:
                    print(f"❌ Échec définitif après {max_retries} tentatives.")
                    raise e
    return wrapper
