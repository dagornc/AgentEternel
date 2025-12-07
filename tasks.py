from crewai import Task
from agents import RecruiterAgent, DevilsAdvocate, Synthesizer, create_expert_agent

from models import ExpertList

def recruit_task(agent, input_query):
    """
    Creates a task for recruiting experts based on the input query.

    Args:
        agent (Agent): The agent responsible for this task (Recruiter).
        input_query (str): The problem statement or query to analyze.

    Returns:
        Task: A CrewAI Task object configured for recruiting experts.
    """
    return Task(
        description=f"Analyze the input: '{input_query}'. Define the optimal team of experts to solve this problem. "
                    f"Choose between 3 and 6 experts depending on the complexity. "
                    f"For each expert, provide: Name, Role, Bias, and Signature Skill. "
                    f"IMPORTANT: If the task involves research, YOU MUST include a 'Research Librarian' expert specialized in searching repositories like hal.science, arxiv.org, researchgate.net, gutemberg.org, zenodo.org. "
                    f"Also include a final member: The Devil's Advocate (Reviewer 2). "
                    f"Return the list of experts in a structured JSON format.",
        expected_output="A list of experts.",
        agent=agent,
        output_pydantic=ExpertList
    )

def hypothesis_task(agent, input_query):
    """
    Creates a task for generating a hypothesis.

    Args:
        agent (Agent): The expert agent generating the hypothesis.
        input_query (str): The problem statement.

    Returns:
        Task: A CrewAI Task object for hypothesis generation.
    """
    return Task(
        description=f"Basé sur l'entrée '{input_query}', générez une hypothèse initiale ou une solution. "
                    f"Utilisez votre rôle et biais spécifiques. Ne soyez pas encore d'accord avec les autres. "
                    f"Utilisez le jargon technique et des références théoriques. "
                    f"Si vous utilisez des outils de recherche, faites-le SEQUENTIELLEMENT (un par un), ne jamais appeler plusieurs outils en même temps.",
        expected_output="Une proposition d'hypothèse ou de solution détaillée.",
        agent=agent
    )

def debate_task(agent, hypotheses, input_query):
    """
    Creates a task for debating the proposed hypotheses.

    Args:
        agent (Agent): The Devil's Advocate agent.
        hypotheses (List[Dict]): A list of hypotheses from the experts.
        input_query (str): The original problem statement.

    Returns:
        Task: A CrewAI Task object for the debate phase.
    """
    hypotheses_text = "\n\n".join([f"{h['expert_name']}: {h['hypothesis']}" for h in hypotheses])
    return Task(
        description=f"Examinez les hypothèses suivantes pour le problème '{input_query}' :\n{hypotheses_text}\n\n"
                    f"Critiquez-les agressivement. Identifiez les hallucinations, les erreurs de corrélation/causalité et les biais méthodologiques. "
                    f"Mettez les experts au défi.",
        expected_output="Une critique des hypothèses proposées, soulignant les défauts et exigeant des clarifications.",
        agent=agent
    )

from models import ExpertList, SynthesisReport

# ... (rest of imports)

def synthesis_task(agent, debate_minutes, hypotheses, input_query):
    """
    Creates a task for synthesizing the final solution.

    Args:
        agent (Agent): The Synthesizer agent.
        debate_minutes (str): The critique from the debate phase.
        hypotheses (List[Dict]): The original hypotheses.
        input_query (str): The original problem statement.

    Returns:
        Task: A CrewAI Task object for the synthesis phase.
    """
    return Task(
        description=f"Analysez les minutes du débat et les hypothèses originales pour '{input_query}'. "
                    f"Minutes du Débat :\n{debate_minutes}\n\n"
                    f"Action: Synthétisez uniquement les informations fournies. N'utilisez AUCUN outil de recherche externe. "
                    f"Rejetez les idées invalides. Fusionnez les idées survivantes en une solution unifiée. "
                    f"Attribuez un score de confiance (0-100%) basé sur la robustesse du débat. "
                    f"SI le score est inférieur à 80%, listez précisément les 'Knowledge Gaps'. "
                    f"Générez également un code Mermaid.js (graph TD). "
                    f"FORMAT: Vous DEVEZ répondre UNIQUEMENT avec un objet JSON valide correspondant à la structure suivante. "
                    f"Assurez-vous d'échapper correctement les sauts de ligne (\\n) et de ne PAS utiliser de caractères de contrôle interdits.\n"
                    f"{{ \"solution\": \"...\", \"confidence_score\": 0.0, \"knowledge_gaps\": [\"...\"], \"visualization_code\": \"...\" }}",
        expected_output="Un objet JSON valide.",
        agent=agent
    )

def cross_pollination_task(agent, current_hypothesis, other_hypotheses, input_query):
    """
    Creates a task for cross-pollinating ideas between experts.

    Args:
        agent (Agent): The expert agent performing the cross-pollination.
        current_hypothesis (str): The expert's own initial hypothesis.
        other_hypotheses (list): List of hypotheses from other experts.
        input_query (str): The original problem statement.

    Returns:
        Task: A CrewAI task for enriching the hypothesis.
    """
    others_text = "\n\n".join([f"- {h['expert_name']} ({h.get('role', 'Expert')}): {h['hypothesis']}" for h in other_hypotheses])
    
    return Task(
        description=f"Vous êtes {agent.role}. Vous avez proposé une hypothèse pour '{input_query}'.\n"
                    f"Voici les hypothèses de vos collègues :\n{others_text}\n\n"
                    f" VOTRE TÂCHE : Enrichissez votre propre hypothèse en vous inspirant des concepts des autres. "
                    f"Cherchez des analogies, des ponts ou des fusions transdisciplinaires. "
                    f"Ne changez pas votre domaine d'expertise, mais intégrez intelligemment les idées des autres pour combler vos propres lacunes. "
                    f"Citez explicitement de qui vous vous inspirez (ex: 'Comme le suggère le Physicien...').",
        expected_output="Une version enrichie et transdisciplinaire de votre hypothèse originale.",
        agent=agent
    )
