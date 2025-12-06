# Nexus-Science Agent 🔬

**Nexus-Science Agent** (anciennement AgentEternel) est un système multi-agents collaboratif conçu pour simuler une "Société de l'Esprit". Il orchestre des agents spécialisés pour résoudre des problèmes de recherche complexes, générer des hypothèses, débattre et synthétiser des solutions optimales.

## 🚀 Fonctionnalités

Le système suit un processus rigoureux en quatre phases :

1.  **Recrutement (Chief of Staff)** : Analyse la requête de l'utilisateur et recrute les experts les plus pertinents pour la tâche.
2.  **Hypothèse (Experts)** : Chaque expert génère des hypothèses basées sur son domaine d'expertise, incluant une évaluation de la faisabilité et de l'impact.
3.  **Débat (Analyst)** : Un analyste critique examine les hypothèses, identifie les conflits et les synergies, et synthétise les points clés du débat.
4.  **Synthèse (Synthesizer)** : Produit une solution finale complète, notée avec un score de confiance, intégrant les meilleures idées du débat.

## 🛠 Technologies

Ce projet utilise une stack moderne pour l'IA et l'orchestration :

*   **[LangGraph](https://langchain-ai.github.io/langgraph/)** : Pour l'orchestration du flux de travail cyclique et la gestion de l'état.
*   **[LangChain](https://www.langchain.com/)** : Pour l'interaction avec les modèles de langage (LLMs).
*   **[CrewAI](https://www.crewai.com/)** : (Inclus dans les dépendances, utilisé pour la structuration initiale des agents).
*   **[Streamlit](https://streamlit.io/)** : Pour l'interface utilisateur interactive et la visualisation.
*   **[OpenAI API](https://openai.com/)** : Moteur d'intelligence (GPT-4 recommandé).
*   **Sphinx** : Pour la génération de documentation technique.

## 📦 Installation

### Prérequis

*   Python 3.9+
*   Une clé API OpenAI valide.

### Étapes

1.  **Cloner le dépôt** :
    ```bash
    git clone <votre-repo-url>
    cd AgentEternel
    ```

2.  **Créer un environnement virtuel** (recommandé) :
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # Sur macOS/Linux
    # .venv\Scripts\activate  # Sur Windows
    ```

3.  **Installer les dépendances** :
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configuration Environnement** :
    Créez un fichier `.env` à la racine du projet et ajoutez votre clé API :
    ```
    OPENAI_API_KEY=sk-votre-cle-api-ici
    ```

## 🖥 Usage

### Interface Web (Streamlit)

C'est la méthode recommandée pour visualiser le processus.

1.  **Lancer l'application** :
    ```bash
    ./launch_app.sh
    # OU
    streamlit run streamlit_app.py
    ```

2.  **Utilisation** :
    *   Ouvrez votre navigateur à l'adresse indiquée (généralement `http://localhost:8501`).
    *   Configurez la **Température** et le **Score de Confiance** dans la barre latérale.
    *   Entrez votre requête de recherche (ex: "Concevoir un système de purification d'eau autonome").
    *   Cliquez sur **Start Research**.
    *   Suivez l'évolution du graphe d'agents et les rapports d'étape en temps réel.

### Ligne de Commande (CLI)

Pour une exécution rapide sans interface graphique :

```bash
python main.py
```
*Note : Modifiez la variable `input_query` dans `main.py` pour changer la requête.*

## 📂 Structure du Projet

*   `agents.py` : Définition des prompts et des rôles des agents (Recruteur, Experts, Analyste, Synthétiseur).
*   `graph.py` : Définition du graphe d'états LangGraph (StateGraph) et de la logique de transition.
*   `tasks.py` : Fonctions exécutant les tâches spécifiques de chaque nœud du graphe.
*   `models.py` : Modèles de données Pydantic pour structurer les échanges (Hypothèses, Rapport de Débat, etc.).
*   `state.py` : Définition de l'état global de l'application (`AgentGraphState`).
*   `streamlit_app.py` : Interface utilisateur principale.
*   `visualization.py` : Logique de visualisation du graphe dynamique.
*   `docs/` : Documentation Sphinx.

## 📚 Documentation

La documentation technique complète est générée avec Sphinx.

Pour la générer localement :

```bash
cd docs
make html
```
Ouvrez ensuite `docs/_build/html/index.html` dans votre navigateur.

## 🤝 Contribuer

Les contributions sont les bienvenues !
1.  Forkez le projet.
2.  Créez votre branche (`git checkout -b feature/AmazingFeature`).
3.  Committez vos changements (`git commit -m 'Add some AmazingFeature'`).
4.  Poussez vers la branche (`git push origin feature/AmazingFeature`).
5.  Ouvrez une Pull Request.

## 📄 Licence

Distribué sous la licence MIT. Voir `LICENSE` pour plus d'informations.
