import json

# Colors - Professional Palette (Pastel/Modern on Dark)
COLOR_ACTIVE = "#10B981" # Emerald 500
COLOR_INACTIVE = "#6B7280" # Cool Gray 500
COLOR_BG_CARD = "#1F2937" # Gray 800
COLOR_BORDER = "#374151" # Gray 700

COLOR_RECRUITER = "#F59E0B" # Amber 500
COLOR_EXPERT = "#3B82F6" # Blue 500
COLOR_DA = "#EF4444" # Red 500
COLOR_SYNTHESIZER = "#8B5CF6" # Violet 500
COLOR_SESSION = "#EC4899" # Pink 500 (For Session Node)

# Icons
ICONS = {
    "Recruiter": "🤝",
    "Expert": "🔬",
    "Devil's Advocate": "😈",
    "Synthesizer": "🧠",
    "Session": "💡",
    "Default": "👤"
}

def get_agent_card(name, role, icon, color, active=False):
    """
    Generates an 'n8n-style' HTML Card for a node.
    """
    active_class = "active" if active else ""
    border_color = color if active else COLOR_BORDER
    opacity = "1.0" if active else "0.7"
    
    # CSS defined in render_dagre_graph
    html = f"""
    <div class="agent-card {active_class}" style="border-left-color: {color}; border-color: {border_color}; opacity: {opacity};">
        <div class="card-icon" style="background-color: {color}20; color: {color};">{icon}</div>
        <div class="card-content">
            <div class="card-title">{name}</div>
            <div class="card-role">{role}</div>
        </div>
        <div class="card-status"></div>
    </div>
    """
    return html.replace("\n", "")

def get_agent_tooltip(role, goal, backstory, skill, bias):
    return f"<b>Role:</b> {role}<br><b>Goal:</b> {goal}<br><b>Skill:</b> {skill}<br><b>Bias:</b> {bias}<br><i>{backstory[:100]}...</i>"

def update_node_visuals(node, active):
    """Refreshes the node's HTML label based on state."""
    # We reconstruct the label because state changes (color/border) act on the HTML 
    # and Dagre-D3 needs the label string updated to re-render inside the SVG foreignObject.
    
    # Parse basic data that we hopefully stored
    name = node.get('meta_name', node['id'])
    role = node.get('meta_role', 'Agent')
    color = node.get('meta_color', "#ccc")
    icon = node.get('meta_icon', "👤")
    
    node['label'] = get_agent_card(name, role, icon, color, active)
    
    if active:
        node['cssClass'] = "active-node"
    else:
        node['cssClass'] = ""

def update_graph_state(key, value, nodes, edges):
    """
    Updates graph using Hub-and-Spoke topology and Card Visuals.
    """
    
    def get_node(nid):
        return next((n for n in nodes if n['id'] == nid), None)

    # 1. Reset all nodes visual state (inactive)
    for node in nodes:
        if not node.get('isCluster'):
            update_node_visuals(node, active=False)
    
    # Reset edges
    for edge in edges:
        edge['cssClass'] = ""

    # --- RECRUIT ---
    if key == "recruit":
        # Recruiter Node
        if not get_node("Recruiter"):
            # Should have been initialized, but just in case
            pass 
        else:
            recruiter = get_node("Recruiter")
            recruiter['meta_role'] = "Chief of Staff" # Update role
            update_node_visuals(recruiter, active=False) # Done

        # Create Cluster
        cluster_id = "cluster_experts"
        if not get_node(cluster_id):
            nodes.append({
                "id": cluster_id,
                "label": "Research Team",
                "isCluster": True,
                "cssClass": "cluster",
                "style": "fill: #2D3748; stroke: #4B5563; rx: 10; ry: 10;"
            })

        for expert in value['experts']:
            eid = expert['name']
            if not get_node(eid):
                role = expert.get('role', 'Expert')
                tooltip = get_agent_tooltip(role, "Solve", expert.get('backstory',''), expert.get('skill',''), expert.get('bias',''))
                icon = ICONS.get("Expert", "🔬")
                
                # Create Node Meta Data
                new_node = {
                    "id": eid,
                    "meta_name": eid,
                    "meta_role": role,
                    "meta_color": COLOR_EXPERT,
                    "meta_icon": icon,
                    "title": tooltip,
                    "parent": cluster_id,
                    "shape": "rect", # Important for HTML labels in Dagre
                    "padding": 0 # Let CSS handle padding
                }
                # Initial visual state
                update_node_visuals(new_node, active=True)
                nodes.append(new_node)
                
                # Edge Recruiter -> Expert
                edges.append({"source": "Recruiter", "target": eid, "label": "recruits", "cssClass": "active"})
            else:
                 # Reactivate
                 n = get_node(eid)
                 update_node_visuals(n, active=True)
                 # Edge
                 edge = next((e for e in edges if e['source'] == "Recruiter" and e['target'] == eid), None)
                 if edge: edge['cssClass'] = "active"

    # --- HYPOTHESIS ---
    elif key == "hypothesis":
        cluster_id = "cluster_experts"
        for node in nodes:
            if node.get('parent') == cluster_id:
                update_node_visuals(node, active=True)

    # --- CROSS POLLINATION (HUB) ---
    elif key == "cross_pollination":
        # Create "Brainstorming Session" Hub Node
        hub_id = "Session_Hub"
        if not get_node(hub_id):
            new_node = {
                "id": hub_id,
                "meta_name": "Brainstorming",
                "meta_role": "Collaboration",
                "meta_color": COLOR_SESSION,
                "meta_icon": ICONS["Session"],
                "title": "Experts exchange ideas and refine hypotheses.",
                "shape": "rect"
            }
            update_node_visuals(new_node, active=True)
            nodes.append(new_node)
        else:
            n = get_node(hub_id)
            update_node_visuals(n, active=True)
            
        # Draw Spokes: Expert -> Hub
        # value['hypotheses'] contains experts
        for item in value['hypotheses']:
            ename = item['expert_name']
            # Edge Expert -> Hub
            edge_key = f"{ename}->{hub_id}"
            edge = next((e for e in edges if e['source'] == ename and e['target'] == hub_id), None)
            if not edge:
                 edges.append({"source": ename, "target": hub_id, "label": "shares", "cssClass": "active"})
            else:
                 edge['cssClass'] = "active"
            
            # Active Expert
            exp = get_node(ename)
            if exp: update_node_visuals(exp, active=True)

    # --- DEBATE ---
    elif key == "debate":
        da_id = "DevilsAdvocate"
        if not get_node(da_id):
            new_node = {
                "id": da_id,
                "meta_name": "Devil's Advocate",
                "meta_role": "Critic",
                "meta_color": COLOR_DA,
                "meta_icon": ICONS["Devil's Advocate"],
                "title": "Critiques the pool of ideas.",
                "shape": "rect"
            }
            update_node_visuals(new_node, active=True)
            nodes.append(new_node)
        else:
            n = get_node(da_id)
            update_node_visuals(n, active=True)
            
        # Edge Hub -> DA (The collective output goes to DA)
        # Or Experts -> DA if Hub doesn't exist (fallback)
        hub_id = "Session_Hub"
        if get_node(hub_id):
             edge = next((e for e in edges if e['source'] == hub_id and e['target'] == da_id), None)
             if not edge:
                 edges.append({"source": hub_id, "target": da_id, "label": "reviews", "cssClass": "active"})
             else:
                 edge['cssClass'] = "active"
        else:
             # Fallback if step skipped
             pass

    # --- SYNTHESIS ---
    elif key == "synthesis":
        syn_id = "Synthesizer"
        if not get_node(syn_id):
            new_node = {
                "id": syn_id,
                "meta_name": "Synthesizer",
                "meta_role": "Decision Maker",
                "meta_color": COLOR_SYNTHESIZER,
                "meta_icon": ICONS["Synthesizer"],
                "title": "Final Synthesis and Report",
                "shape": "rect"
            }
            update_node_visuals(new_node, active=True)
            nodes.append(new_node)
        else:
            n = get_node(syn_id)
            update_node_visuals(n, active=True)
            
        # Edge DA -> Synthesizer
        edge = next((e for e in edges if e['source'] == "DevilsAdvocate" and e['target'] == syn_id), None)
        if not edge:
            edges.append({"source": "DevilsAdvocate", "target": syn_id, "label": "reports", "cssClass": "active"})
        else:
            edge['cssClass'] = "active"
            
        # Feedback Loop
        iterations = value.get('iterations', 0)
        confidence = value.get('confidence_score', 0)
        
        if iterations > 0 and confidence < 80:
             # Loop back to Hub or Experts Cluster?
             # Hub is cleaner if it exists.
             target = "Session_Hub" if get_node("Session_Hub") else "cluster_experts"
             
             edge = next((e for e in edges if e['source'] == syn_id and e['target'] == target), None)
             if not edge:
                  edges.append({"source": syn_id, "target": target, "label": "refines", "cssClass": "feedback"})
             else:
                  edge['cssClass'] = "feedback"

    return nodes, edges

def render_dagre_graph(nodes, edges, height=550):
    """
    Renders n8n-style graph.
    """
    nodes_json = json.dumps(nodes)
    edges_json = json.dumps(edges)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://d3js.org/d3.v5.min.js"></script>
        <script src="https://dagrejs.github.io/project/dagre-d3/latest/dagre-d3.min.js"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
        <style>
             /* RESET */
             * {{ box-sizing: border-box; }}
            
            body {{
                margin: 0;
                overflow: hidden;
                background-color: #111827; /* Gray 900 */
                font-family: 'Inter', sans-serif;
            }}
            
            /* SVG Container */
            svg {{
                width: 100vw;
                height: {height}px;
            }}
            
            /* --- NODE CARD STYLING (n8n style) --- */
            .agent-card {{
                width: 200px;
                background-color: #1F2937; /* Gray 800 */
                border: 1px solid #374151;
                border-left-width: 4px; /* Colored accent */
                border-radius: 8px;
                padding: 12px;
                display: flex;
                align-items: center;
                gap: 12px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
                transition: all 0.3s ease;
                color: white;
            }}
            
            .agent-card.active {{
                box-shadow: 0 0 15px rgba(16, 185, 129, 0.3); /* Green Glow */
                border-color: #10B981;
            }}

            .agent-card.active .card-icon {{
                animation: spin 4s linear infinite;
            }}
            
            .card-icon {{
                font-size: 20px;
                width: 36px;
                height: 36px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 6px;
                flex-shrink: 0;
            }}
            
            .card-content {{
                flex-grow: 1;
                overflow: hidden;
            }}
            
            .card-title {{
                font-weight: 600;
                font-size: 14px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }}
            
            .card-role {{
                font-size: 11px;
                color: #9CA3AF; /* Gray 400 */
                margin-top: 2px;
            }}
            
            /* Status Dot */
            .card-status {{
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background-color: #374151;
            }}
            .agent-card.active .card-status {{
                background-color: #10B981;
                box-shadow: 0 0 5px #10B981;
            }}

            /* --- CLUSTERS --- */
            g.cluster rect {{
                fill: #1F2937;
                stroke: #4B5563;
                stroke-width: 1px;
                rx: 8;
                ry: 8;
                opacity: 0.5;
            }}
            
            /* --- EDGES --- */
            .edgePath path {{
                stroke: #6B7280; /* Gray 500 */
                stroke-width: 2px;
                fill: none;
            }}
            .edgePath.active path {{
                stroke: #10B981; /* Emerald */
                stroke-width: 2px;
                animation: flow 1s linear infinite;
            }}
            .edgePath.feedback path {{
                stroke: #F59E0B; /* Amber */
                stroke-dasharray: 5, 5;
                animation: flow-reverse 2s linear infinite;
            }}
            
            @keyframes flow {{
                to {{ stroke-dashoffset: -20; }}
            }}
             @keyframes flow-reverse {{
                to {{ stroke-dashoffset: 20; }}
            }}
            @keyframes spin {{ 
                100% {{ transform: rotate(360deg); }} 
            }}
            
            /* --- CONTROLS --- */
            .controls {{
                position: absolute;
                bottom: 20px;
                right: 20px;
                display: flex;
                gap: 8px;
                background: #1F2937;
                padding: 8px;
                border-radius: 8px;
                border: 1px solid #374151;
            }}
            .btn {{
                background: #374151;
                border: none;
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
                font-weight: 600;
            }}
            .btn:hover {{ background: #4B5563; }}

            /* HIDE DAGRE RECT for HTML NODES */
            g.node rect {{
                fill: transparent;
                stroke: none;
            }}
        </style>
    </head>
    <body>
        <div class="controls">
            <button class="btn" onclick="resetZoom()">Fit</button>
            <button class="btn" onclick="toggleDir()">Rotate</button>
            <button class="btn" onclick="dl()">SVG</button>
        </div>
        
        <svg id="svg-canvas"><g></g></svg>

        <script>
            try {{
                // SETUP GRAPH
                var g = new dagreD3.graphlib.Graph({{compound:true}})
                    .setGraph({{
                        rankdir: 'LR',
                        nodesep: 50,    // Horizontal space
                        ranksep: 80,    // Vertical space (between layers)
                        marginx: 40,
                        marginy: 40
                    }})
                    .setDefaultEdgeLabel(function() {{ return {{}}; }});

                var nodes = {nodes_json};
                var edges = {edges_json};

                // NODES
                nodes.forEach(function(node) {{
                    if (node.isCluster) {{
                        g.setNode(node.id, {{
                            label: node.label,
                            clusterLabelPos: 'top',
                            style: node.style,
                            class: "cluster"
                        }});
                    }} else {{
                        g.setNode(node.id, {{
                            label: node.label,
                            labelType: "html",
                            padding: 0,
                            class: node.cssClass
                        }});
                        if (node.parent) g.setParent(node.id, node.parent);
                    }}
                }});

                // EDGES
                edges.forEach(function(edge) {{
                    g.setEdge(edge.source, edge.target, {{
                        label: "", // Minimalist edges
                        curve: d3.curveBasis, // Smooth curves
                        class: edge.cssClass,
                        arrowhead: 'undirected' // Cleaner look
                    }});
                }});

                // RENDER
                var svg = d3.select("#svg-canvas"),
                    inner = svg.select("g");
                
                var zoom = d3.zoom().on("zoom", function() {{
                    inner.attr("transform", d3.event.transform);
                }});
                svg.call(zoom);

                var render = new dagreD3.render();
                render(inner, g);

                // CENTER
                function centerGraph() {{
                    var initialScale = 0.85;
                    var svgWidth = window.innerWidth;
                    var svgHeight = {height};
                    var graphWidth = g.graph().width;
                    var graphHeight = g.graph().height;
                    
                    var xOffset = (svgWidth - graphWidth * initialScale) / 2;
                    var yOffset = (svgHeight - graphHeight * initialScale) / 2;
                    
                    svg.transition().duration(750).call(
                        zoom.transform,
                        d3.zoomIdentity.translate(xOffset, yOffset).scale(initialScale)
                    );
                }}
                
                centerGraph();
                
                // HELPERS
                window.resetZoom = centerGraph;
                window.dl = function() {{
                    var data = document.getElementById("svg-canvas").outerHTML;
                    var blob = new Blob([data], {{type:"image/svg+xml;charset=utf-8"}});
                    var url = URL.createObjectURL(blob);
                    var a = document.createElement("a");
                    a.href = url; a.download = "graph.svg";
                    document.body.appendChild(a); a.click();
                }};
                
                window.toggleDir = function() {{
                    var cur = g.graph().rankdir;
                    g.graph().rankdir = (cur === 'LR' ? 'TB' : 'LR');
                    render(inner, g);
                    centerGraph();
                }}

            }} catch (e) {{
                document.body.innerHTML = "<h3 style='color:white;padding:20px'>Render Error: " + e.message + "</h3>";
            }}
        </script>
    </body>
    </html>
    """
    return html
