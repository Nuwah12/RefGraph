import dash
from dash import dcc, html, Input, Output, State
import dash_cytoscape as cyto
import networkx as nx
import traceback
import sys

sys.path.append("./src")
from OpenAlexRefGraph import OpenAlexRefGraph  # make sure this is error-free

app = dash.Dash(__name__)
cyto.load_extra_layouts()

app.layout = html.Div([
    html.H1("Citation Graph Builder"),

    dcc.Input(
        id='doi-input',
        type='text',
        placeholder='Enter DOI...',
        debounce=True,
        style={'width': '50%'}
    ),
    dcc.Input(
        id='max-nodes',
        type='number',
        placeholder='Max nodes',
        debounce=True,
        style={'width': '7%'}
    ),
    html.Button('Build Graph', id='build-button', n_clicks=0),

    cyto.Cytoscape(
        id='cytoscape-graph',
        layout={'name': 'breadthfirst', 'animate': True, 'nodeRepulsion': 5000, 'idealEdgeLength': 10},
        style={'width': '100%', 'height': '600px'},
        elements=[],
        stylesheet=[
            {'selector': 'node', 'style': {'label': 'data(label)', 'color': 'black'}},
            {'selector': 'edge', 'style': {'curve-style': 'bezier', 'target-arrow-shape': 'triangle'}}
        ]
    ),
    html.Div(id='node-info', style={"marginTop": "10px", "whiteSpace": "pre-line"})
])

@app.callback(
    Output('cytoscape-graph', 'elements'),
    Input('build-button', 'n_clicks'),
    Input('max-nodes', 'value'),
    State('doi-input', 'value')
)
def update_graph(n_clicks, max_nodes, doi_input):
    if not doi_input:
        return []

    try:
        print(f"Building graph for DOI: {doi_input}")
        refgraph = OpenAlexRefGraph(doi_input, max_nodes=max_nodes)

        G = refgraph.refg
        metadata = refgraph.md

        if not G or len(G.nodes) == 0:
            print("Graph is empty.")
            return []

        # Compute citation count (out-degree) and normalize for color scale
        max_citations = max((G.out_degree(n) for n in G.nodes), default=1)

        elements = []
        for node in G.nodes():
            meta = metadata.get(node, {})
            title = meta.get("title", node)
            year = meta.get("year", "N/A")
            citations = G.out_degree(node)

            elements.append({
                'data': {
                    'id': node,
                    'label': title[:50] if title else node[:12],
                    'year': year,
                    'citations': citations
                },
                'style': {
                    'width': 30,
                    'height': 30
                }
            })

        for u, v in G.edges():
            elements.append({
                'data': {'source': u, 'target': v}
            })

        print(f"Generated graph with {len(G.nodes)} nodes and {len(G.edges)} edges.")
        return elements

    except Exception as e:
        print("Exception occurred during graph build:")
        traceback.print_exc()
        return [{'data': {'id': 'error', 'label': 'Graph build failed'}}]


@app.callback(
    Output('node-info', 'children'),
    Input('cytoscape-graph', 'mouseoverNodeData')
)
def display_node_info(data):
    if data:
        return f"Title: {data.get('label', '')}\nYear: {data.get('year', 'N/A')}"
    return "Hover over a node to see info."

if __name__ == '__main__':
    app.run_server(debug=True)