from crewai import Agent, LLM
from crewai.tools import BaseTool
from crewai_tools import SerperDevTool
from langchain_community.tools import DuckDuckGoSearchRun
from tools import ArxivTool, HalTool
import os

# Assuming OPENAI_API_KEY is set in environment
# You might need to adjust the model name based on what's available/cost
DEFAULT_MODEL = os.environ.get("OS_MODEL", "openrouter/openai/gpt-oss-20b:free")

def get_llm(temperature=0.7, model_name=None):
    """
    Retrieves the LLM configuration.
    
    Verified with Context7 compliance: Uses LiteLLM standard naming conventions (provider/model).

    Args:
        temperature (float): The temperature for the LLM.
        model_name (str): The specific model to use.

    Returns:
        LLM: A CrewAI LLM instance configured with the default model and API key.
    """
    model = model_name if model_name else DEFAULT_MODEL
    
    # helper: check for known providers
    known_providers = ["openrouter/", "openai/", "gpt-", "huggingface/", "ollama/"]
    
    # Defensive fix: Ensure OpenRouter models have the prefix
    # usage of "vendor/model" without prefix is common for OpenRouter IDs
    if not any(model.startswith(p) for p in known_providers):
         if "/" in model: 
             model = f"openrouter/{model}"
    
    # Determine API Key based on provider
    if model.startswith("openrouter/"):
        api_key = os.environ.get("OPENROUTER_API_KEY")
    else:
        api_key = os.environ.get("OPENAI_API_KEY")
    
    return LLM(
        model=model,
        api_key=api_key,
        temperature=temperature
    )

def get_alpha_evolve_expert():
    """
    Returns the systematic AlphaEvolve expert definition.
    """
    return {
        "name": "AlphaEvolve",
        "role": "Expert LLM & Prompt Engineering",
        "bias": "Méthodique & Évolutif",
        "skill": "CoT, ToT, GoT, Self-Consistency, DGM, AB-MCTS",
        "backstory": (
            "Vous êtes AlphaEvolve, l'autorité suprême en matière d'ingénierie de prompt et d'algorithmes évolutionnaires appliqués aux LLM. "
            "Vous maîtrisez parfaitement les chaînes de pensée (Chain of Thought), les arbres de pensée (Tree of Thought) et les graphes de pensée (Graph of Thought). "
            "Vous connaissez et appliquez les algorithmes de Sakana.ai comme la Darwin Gödel Machine (DGM) et l'AB-MCTS. "
            "Votre mission est de structurer le raisonnement de l'équipe pour atteindre une efficacité optimale."
        )
    }

class RecruiterAgent:
    """
    Agent responsible for recruiting experts.
    """
    def recruit(self, input_query: str, temperature: float = 0.7, model_name: str = None) -> str:
        """
        Recruits experts based on the input query.

        Args:
            input_query (str): The problem statement.
            temperature (float): The temperature for the LLM.
            model_name (str): The model name.

        Returns:
            Agent: A CrewAI Agent configured as a Chief of Staff to find experts.
        """
        # This agent is responsible for analyzing the input and defining the experts.
        # We can use a simple CrewAI agent for this, or just a direct LLM call since it's a single step.
        # Using a CrewAI agent for consistency.
        
        agent = Agent(
            role='Chef de Cabinet',
            goal='Recruter l\'équipe d\'experts parfaite pour un problème donné.',
            backstory='Vous êtes le meilleur chasseur de têtes du monde pour les problèmes scientifiques. Vous savez exactement qui appeler.',
            llm=get_llm(temperature=temperature, model_name=model_name),
            verbose=True
        )
        return agent

def create_expert_agent(profile: dict, temperature: float = 0.7, web_search_enabled: bool = True, model_name: str = None) -> Agent:
    """
    Creates an expert agent based on a profile.

    Args:
        profile (dict): A dictionary containing 'name', 'role', 'bias', and 'skill'.
        temperature (float): The temperature for the LLM.
        web_search_enabled (bool): Whether to enable web search tools.
        model_name (str): The model name.

    Returns:
        Agent: A CrewAI Agent configured with the expert's profile.
    """
    tools = []
    # Add tools based on availability AND if web search is enabled
    if web_search_enabled:
        if os.environ.get("SERPER_API_KEY"):
             tools.append(SerperDevTool())
        else:
             # Fallback to DDG if no Serper key
             # Wrap LangChain tool for CrewAI compatibility using BaseTool class
             class DDGTool(BaseTool):
                 name: str = "DuckDuckGo Search"
                 description: str = "Useful for searching the internet for information."
                 
                 def _run(self, query: str) -> str:
                     return DuckDuckGoSearchRun().run(query)

             tools.append(DDGTool())

        # Add Academic Tools if the role suggests research or if it's the Librarian
        if "research" in profile['role'].lower() or "recherche" in profile['role'].lower() or "librarian" in profile['name'].lower() or "chercheur" in profile['name'].lower() or "alphaevolve" in profile['name'].lower():
            tools.append(ArxivTool())
            tools.append(HalTool())

    return Agent(
        role=profile['role'],
        goal=f"Résoudre le problème en utilisant votre expertise en {profile['role']} et votre compétence en {profile['skill']}. IMPORTANT: VOUS NE POUVEZ UTILISER QU'UN SEUL OUTIL À LA FOIS. NE JAMAIS lister plusieurs outils dans une seule Action.",
        backstory=f"Vous êtes {profile['name']}. Vous êtes un {profile['bias']}. Votre compétence signature est {profile['skill']}. RAPPEL: Une seule action d'outil à la fois.",
        llm=get_llm(temperature=temperature, model_name=model_name),
        tools=tools,
        verbose=True
    )

class DevilsAdvocate:
    """
    Agent responsible for critiquing hypotheses.
    """
    def get_agent(self, temperature: float = 0.7, model_name: str = None) -> Agent:
        """
        Creates the Devil's Advocate agent.

        Args:
            temperature (float): The temperature for the LLM.
            model_name (str): The model name.

        Returns:
            Agent: A CrewAI Agent configured as the Devil's Advocate.
        """
        return Agent(
            role="Avocat du Diable",
            goal="Critiquer les hypothèses et trouver des failles, des sophismes et un manque de preuves.",
            backstory="Vous êtes le Reviewer 2. Vous êtes sceptique, rigoureux et vous détestez les affirmations non fondées. Vous recherchez les hallucinations, la confusion corrélation/causalité et les biais méthodologiques.",
            llm=get_llm(temperature=temperature, model_name=model_name),
            verbose=True
        )

class Synthesizer:
    """
    Agent responsible for synthesizing the final solution.
    """
    def get_agent(self, temperature: float = 0.7, model_name: str = None) -> Agent:
        """
        Creates the Synthesizer agent.

        Args:
            temperature (float): The temperature for the LLM.
            model_name (str): The model name.

        Returns:
            Agent: A CrewAI Agent configured as the Synthesizer.
        """
        return Agent(
            role="Synthétiseur",
            goal="Synthétiser le débat en une solution finale et attribuer un score de confiance.",
            backstory="Vous êtes le décideur ultime. Vous écoutez toutes les parties, rejetez les idées invalides et fusionnez les meilleures en une solution unifiée.",
            llm=get_llm(temperature=temperature, model_name=model_name),
            tools=[],
            verbose=True
        )
