# AgentEternel (Nexus-Science Agent)

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-green.svg)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![AI](https://img.shields.io/badge/AI-Multi--Agent-purple.svg)

Système multi-agents collaboratif conçu pour simuler une "Société de l'Esprit". Il orchestre des agents spécialisés pour résoudre des problèmes de recherche complexes, générer des hypothèses, débattre et synthétiser des solutions optimales.

## 📋 Table des matières
- [Présentation](#présentation)
- [Architecture multi-agents](#architecture-multi-agents)
- [Technologies](#technologies)
- [Installation](#installation)
- [Usage](#usage)
- [Structure du projet](#structure-du-projet)
- [Documentation](#documentation)

## 🎯 Présentation
**AgentEternel** est un framework de recherche autonome à base d'agents IA. L'architecture s'inspire du concept de "Société de l'Esprit" de Marvin Minsky : plusieurs agents spécialisés collaborent, débattent et fusionnent leurs conclusions pour produire des réponses exhaustives et nuancées.

Contraîrement aux chatbots classiques, ce système **ne se contente pas de répondre** : il pense, planifie, débat et s'auto-critique pour converger vers la meilleure solution.

## 🤖 Architecture multi-agents
Le pipeline suit un processus rigoureux en 4 phases orchestré via **LangGraph** :

```
[Requête Utilisateur]
    ↓
[1. Recruteur (Chief of Staff)] → Sélection des experts optimaux
    ↓
[2. Experts (N agents)] → Génération d'hypothèses spécialisées
    ↓
[3. Analyste] → Débat critique, synergies, conflits
    ↓
[4. Synthétiseur] → Solution finale avec score de confiance
```

### Les rôles des agents :
- **Chief of Staff (Recruteur)** : Analyse la requête et recrute les experts les plus pertinents.
- **Experts** : Chaque expert génère des hypothèses selon son domaine (faisabilité + impact).
- **Analyste** : Examine les hypothèses, identifie conflits et synergies, synthétise le débat.
- **Synthétiseur** : Produit la solution finale avec un score de confiance.

## 🛠 Technologies
| Composant | Outil | Rôle |
|-----------|-------|------|
| Orchestration | LangGraph | Graphe d'états cyclique |
| LLM | OpenAI GPT-4 | Moteur de raisonnement |
| Chaines | LangChain | Interactions LLM |
| UI | Streamlit | Interface web interactive |
| Agents | CrewAI | Structuration initiale |
| Docs | Sphinx | Documentation technique |
| Données | Pydantic | Modèles de données |

## 📦 Installation
### Prérequis
- Python 3.9+
- Clé API OpenAI valide

### Étapes
1. Clonez le dépôt :
```bash
git clone https://github.com/dagornc/AgentEternel.git
cd AgentEternel
```

2. Créez un environnement virtuel :
```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
```

3. Installez les dépendances :
```bash
pip install -r requirements.txt
```

4. Configurez l'API :
```bash
cp .env.example .env
# Editez .env et ajoutez : OPENAI_API_KEY=sk-votre-cle
```

## 💻 Usage
### Interface Web (recommandée)
```bash
./launch_app.sh
# OU
streamlit run streamlit_app.py
```
Ouvrez `http://localhost:8501` dans votre navigateur, configurez la température et le score de confiance, puis soumettez votre requête.

### Ligne de commande
```bash
python main.py
```

### Exemples de requêtes
- "Concevoir un système de purification d'eau autonome"
- "Analyser l'impact économique de l'IA sur le marché du travail"
- "Proposer une architecture micro-services pour une application e-commerce à grande échelle"

## 📂 Structure du projet
```
AgentEternel/
├── agents.py          # Définition des rôles et prompts des agents
├── graph.py           # Graphe d'états LangGraph (StateGraph)
├── tasks.py           # Taches spécifiques de chaque nœud
├── models.py          # Modèles Pydantic (Hypothèses, Rapports)
├── state.py           # État global AgentGraphState
├── streamlit_app.py   # Interface utilisateur principale
├── visualization.py   # Visualisation du graphe dynamique
├── check_models.py    # Vérification des modèles disponibles
├── docs/              # Documentation Sphinx
└── tests/             # Tests automatisés
```

## 📚 Documentation
Générez la documentation locale via Sphinx :
```bash
cd docs
make html
# Ouvrez docs/_build/html/index.html
```

## 🧑‍💻 Contribution
1. Forkez le projet.
2. Créez votre branche : `git checkout -b feature/NomFeature`
3. Committez : `git commit -m 'Add NomFeature'`
4. Poussez : `git push origin feature/NomFeature`
5. Ouvrez une Pull Request.

## 📄 Licence
Distribué sous la licence **MIT**.
