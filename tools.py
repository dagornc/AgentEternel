from crewai.tools import BaseTool
import arxiv
import requests

class ArxivTool(BaseTool):
    name: str = "Arxiv Search"
    description: str = "Tire profit de l'API Arxiv pour trouver des papiers de recherche (Preprints). Utile pour les mathématiques, la physique, l'informatique, la biologie quantitative."

    def _run(self, query: str) -> str:
        try:
            search = arxiv.Search(
                query=query,
                max_results=3,
                sort_by=arxiv.SortCriterion.Relevance
            )
            results = []
            for result in search.results():
                results.append(f"Title: {result.title}\nAuthors: {', '.join([a.name for a in result.authors])}\nSummary: {result.summary[:300]}...\nLink: {result.entry_id}\n")
            return "\n".join(results) if results else "Aucun résultat trouvé sur Arxiv."
        except Exception as e:
            return f"Erreur Arxiv: {e}"

class HalTool(BaseTool):
    name: str = "HAL Search"
    description: str = "Recherche sur les Archives Ouvertes HAL (Science Ouverte). Utile pour la recherche académique francophone et internationale dans toutes les disciplines."

    def _run(self, query: str) -> str:
        url = "https://api.archives-ouvertes.fr/search/"
        params = {
            "q": query,
            "wt": "json",
            "fl": "title_s,authFullName_s,abstract_s,uri_s",
            "rows": 3
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            docs = data.get("response", {}).get("docs", [])
            results = []
            for doc in docs:
                title = doc.get("title_s", ["Non spécifié"])[0] if isinstance(doc.get("title_s"), list) else doc.get("title_s", "Non spécifié")
                authors = ", ".join(doc.get("authFullName_s", ["Inconnu"])) if isinstance(doc.get("authFullName_s"), list) else str(doc.get("authFullName_s"))
                abstract_raw = doc.get("abstract_s", ["Pas de résumé"])
                abstract = abstract_raw[0] if isinstance(abstract_raw, list) and abstract_raw else "Pas de résumé"
                link = doc.get("uri_s", "#")
                results.append(f"Titre: {title}\nAuteurs: {authors}\nRésumé: {abstract[:300]}...\nLien: {link}\n")
            return "\n".join(results) if results else "Aucun résultat trouvé sur HAL."
        except Exception as e:
            return f"Erreur lors de la recherche HAL : {e}"
