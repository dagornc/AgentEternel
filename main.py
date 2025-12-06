import os
from dotenv import load_dotenv
from graph import app
from rich.console import Console
from rich.markdown import Markdown

load_dotenv()

console = Console()

from utils import format_output

def main():
    """
    Main entry point for the Nexus-Science application.
    """
    # Ensure API Key is set
    if not os.environ.get("OPENAI_API_KEY"):
        console.print("[bold red]Error: OPENAI_API_KEY not found in environment variables.[/bold red]")
        return

    input_query = "générer un algorithme parfait pour gérer les déplacements d’un essaim de drones sous-marins en mode attaque"
    
    console.print(f"[bold green]Démarrage de Nexus-Science avec l'entrée :[/bold green] {input_query}")
    
    initial_state = {
        "input": input_query,
        "experts": [],
        "hypotheses": [],
        "debate_minutes": "",
        "final_solution": "",
        "confidence_score": 0.0,
        "iterations": 0
    }
    
    # Run the graph
    # Using stream to show progress if needed, or just invoke
    final_state = app.invoke(initial_state)
    
    # Format and print output
    report = format_output(final_state)
    
    console.print(Markdown(report))
    
    # Save to file
    with open("nexus_science_report.md", "w") as f:
        f.write(report)
    console.print("[bold blue]Rapport enregistré dans nexus_science_report.md[/bold blue]")

if __name__ == "__main__":
    main()
