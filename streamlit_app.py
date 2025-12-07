import streamlit as st
import os
import requests
import streamlit.components.v1 as components
from dotenv import load_dotenv
from graph import app
@st.cache_data
def cached_render_dagre_graph(nodes, edges):
    return render_dagre_graph(nodes, edges)

from visualization import update_graph_state, COLOR_ACTIVE, get_agent_tooltip, render_dagre_graph, update_node_visuals, ICONS, COLOR_RECRUITER
from utils import format_output

# Load environment variables
load_dotenv()

def main():
    st.set_page_config(page_title="Nexus-Science Agent", page_icon="🔬", layout="wide")
    
    st.title("🔬 Nexus-Science Agent")
    st.markdown("Collaborative AI research agent simulating a 'Society of the Mind'.")

    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            st.error("OPENAI_API_KEY not found in environment variables.")
            st.info("Please set it in your .env file.")
        else:
            st.success("OpenAI API Key detected.")
            
        # Graph Layout Options - Removed specific layout options as Dagre is now default
        st.info("Using Dagre-D3 for visualization.")

        @st.cache_data(ttl=3600)
        def get_openrouter_free_models():
            """Fetches the list of free models from OpenRouter API."""
            try:
                response = requests.get("https://openrouter.ai/api/v1/models")
                if response.status_code == 200:
                    models = response.json()["data"]
                    # Filter for models with ':free' in ID
                    free_models = [m["id"] for m in models if ":free" in m["id"]]
                    return sorted(free_models)
            except Exception as e:
                print(f"Error fetching models: {e}")
            
            # Fallback list if API fails
            return [
                "google/gemini-2.0-flash-exp:free",
                "meta-llama/llama-3.3-70b-instruct:free",
                "meta-llama/llama-3.1-8b-instruct:free",
                "mistralai/mistral-7b-instruct:free",
                "microsoft/phi-3-medium-128k-instruct:free",
                "openrouter/openai/gpt-oss-20b:free"
            ]

        st.markdown("---")
        st.header("Parameters")
        temperature = st.slider("Model Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.1, help="Controls randomness: 0 is deterministic, 1 is creative.")
        target_confidence = st.slider("Target Confidence Score", min_value=0, max_value=100, value=80, step=5, help="Target score to end the research loop.")
        max_iterations = st.slider("Max Iterations", min_value=1, max_value=10, value=3, step=1, help="Limit the number of feedback loops.")
        web_search = st.checkbox("Enable Web Search", value=True, help="Allow experts to search the internet.")

        
        with st.spinner("Fetching available models..."):
             model_options = get_openrouter_free_models()
        
        # Ensure default legacy model is present or fallback
        default_model = "google/gemini-2.0-flash-exp:free"
        
        # Remove Custom option as per user strict requirement
        # model_options.append("Autre (Custom)...") 
        
        index = 0
        if default_model in model_options:
            index = model_options.index(default_model)
            
        selected_model = st.selectbox("Model", model_options, index=index, help="Select the LLM model to use. Only displaying free models.")
        
        model_name = selected_model
        
        # Ensure openrouter prefix for litellm
        if not model_name.startswith("openrouter/"):
             model_name = f"openrouter/{model_name}"
        
        language = st.selectbox("Output Language", ["Français", "English", "Español", "Deutsch"], help="Language for the final report.")

    # Main input
    query = st.text_area("Enter your research query:", height=100, placeholder="e.g., Generate a perfect algorithm for underwater drone swarm attack mode...")

    if st.button("Start Research", type="primary"):
        if not query:
            st.warning("Please enter a query first.")
            return
        
        if not api_key:
            st.error("Cannot proceed without OpenAI API Key.")
            return
        
        st.session_state['research_started'] = True
        st.session_state['query'] = query # Persist query too if needed
        # Reset research_finished flag if a new research is started
        st.session_state['research_finished'] = False
        
        # Initialize nodes as dictionaries
        st.session_state['nodes'] = [] 
        tooltip = get_agent_tooltip("Chief of Staff", "Recruit Experts", "Headhunter", "Recruitment", "None")
        
        # Create Meta-Data Node compliant with new visualization
        recruiter_node = {
            "id": "Recruiter",
            "meta_name": "Chief of Staff",
            "meta_role": "Recruiter",
            "meta_icon": ICONS.get("Recruiter", "🤝"),
            "meta_color": COLOR_RECRUITER,
            "title": tooltip,
            "shape": "rect",
            "padding": 0
        }
        update_node_visuals(recruiter_node, active=True)
        st.session_state['nodes'].append(recruiter_node)
        st.session_state['edges'] = [] # Reset graph edges


    if st.session_state.get('research_started', False):
        
        # Create containers for real-time updates
        # Status containers removed for cleaner UI as per requirements

        
        # Placeholder for the graph
        st.markdown("### 🕸️ Agent Communication Graph")
        graph_placeholder = st.empty()

        # Initialize Graph State in Session State if not exists
        if 'nodes' not in st.session_state:
            st.session_state['nodes'] = []
            # Initial Node: Recruiter
            tooltip = get_agent_tooltip("Chief of Staff", "Recruit Experts", "Headhunter", "Recruitment", "None")
            
            # Create Meta-Data Node compliant with new visualization
            recruiter_node = {
                "id": "Recruiter",
                "meta_name": "Chief of Staff",
                "meta_role": "Recruiter",
                "meta_icon": ICONS.get("Recruiter", "🤝"),
                "meta_color": COLOR_RECRUITER,
                "title": tooltip,
                "shape": "rect",
                "padding": 0
            }
            update_node_visuals(recruiter_node, active=True)
            st.session_state['nodes'].append(recruiter_node)

        if 'edges' not in st.session_state:
            st.session_state['edges'] = []
        
        try:
            # If research is already finished, just display the results
            if st.session_state.get('research_finished', False):
                # Render Graph
                with graph_placeholder:
                    components.html(cached_render_dagre_graph(st.session_state['nodes'], st.session_state['edges']), height=500)
                
                # Containers updates removed.
                
                if 'final_report' in st.session_state:
                    report = st.session_state['final_report']
                    st.divider()
                    st.success("✨ Recherche Terminée !")
                    
                    with st.container():
                        st.markdown("## 📑 Rapport Final")
                        st.markdown(report)
                    
                    st.markdown("### 💾 Exporter le Rapport")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            label="📥 Télécharger en Markdown",
                            data=report,
                            file_name="nexus_science_report.md",
                            mime="text/markdown",
                            use_container_width=True
                        )
                    with col2:
                        st.download_button(
                            label="📥 Télécharger en Texte Brut",
                            data=report,
                            file_name="nexus_science_report.txt",
                            mime="text/plain",
                            use_container_width=True
                        )
            
            else:
                # Research NOT finished, run the stream
                initial_state = {
                    "input": st.session_state.get('query', query),
                    "experts": [],
                    "hypotheses": [],
                    "debate_minutes": "",
                     "final_solution": "",
                    "confidence_score": 0.0,
                    "target_confidence_score": target_confidence,
                    "temperature": temperature,
                    "max_iterations": max_iterations,
                    "web_search_enabled": web_search,
                    "model_name": model_name,
                    "language": language,
                    "iterations": 0
                }
                
                # Render initial graph
                with graph_placeholder:
                    components.html(cached_render_dagre_graph(st.session_state['nodes'], st.session_state['edges']), height=500)

                # Run the graph with streaming
                import asyncio
                
                state_monitor = initial_state.copy()
                final_state = None
                step_counter = 0
                
                async def run_research():
                    nonlocal state_monitor, final_state, step_counter
                    async for output in app.astream(initial_state):
                        for key, value in output.items():
                            step_counter += 1
                            state_monitor.update(value)
                            
                            # Update Graph State
                            st.session_state['nodes'], st.session_state['edges'] = update_graph_state(
                                key, value, st.session_state['nodes'], st.session_state['edges']
                            )
                            
                            if key == "synthesis":
                                final_state = state_monitor.copy()

                            # Update Graph
                            with graph_placeholder:
                                 components.html(cached_render_dagre_graph(st.session_state['nodes'], st.session_state['edges']), height=500)
                
                asyncio.run(run_research())

                if final_state:
                    # Format output
                    report = format_output(final_state)
                    st.session_state['final_report'] = report
                    st.session_state['research_finished'] = True
                    
                    st.divider()
                    st.success("✨ Recherche Terminée !")
                    
                    with st.container():
                         st.markdown("## 📑 Rapport Final")
                         st.markdown(report)
                         
                    st.markdown("### 💾 Exporter le Rapport")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            label="📥 Télécharger en Markdown",
                            data=report,
                            file_name="nexus_science_report.md",
                            mime="text/markdown",
                            use_container_width=True
                        )
                    with col2:
                        st.download_button(
                            label="📥 Télécharger en Texte Brut",
                            data=report,
                            file_name="nexus_science_report.txt",
                            mime="text/plain",
                            use_container_width=True
                        )
                
        except Exception as e:
            st.error(f"An error occurred: {e}")
            raise e

if __name__ == "__main__":
    main()
