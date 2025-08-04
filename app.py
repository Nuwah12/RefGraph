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

app.layout = html.Div(style={'fontFamily': 'Arial, sans-serif', 'padding': '20px', 'backgroundColor': '#eceff4'}, 
                      children=[
                html.H1("Citation Graph Builder"),

                html.Div(
                    dcc.Input(
                        id='doi-input',
                        type='text',
                        placeholder='Enter DOI...',
                        debounce=True,
                        style={'width': '50%'}
                    ),
                    style={'marginBottom': '15px'}
                ),
                html.Div(
                    dcc.Input(
                        id='max-nodes',
                        type='number',
                        placeholder='Max nodes',
                        debounce=True,
                        style={'width': '7%'}
                    ),
                    style={'marginBottom': '15px'}
                ),
                html.Button('Build Graph', id='build-button', n_clicks=0),

                cyto.Cytoscape(
                    id='cytoscape-graph',
                    layout={'name': 'preset', 
                            'animate': True},
                    zoom=1,                # initial zoom level
                    minZoom=0.5,           # minimum allowed zoom level
                    maxZoom=2,             # maximum allowed zoom level
                    pan={'x': 0, 'y': 0},  # initial pan position
                    style={'width': '100%', 'height': '600px'},
                    elements=[],
                    stylesheet=[
                        {'selector': 'node', 'style': {'label': 'data(label)', 'color': 'black'}},
                        {'selector': 'edge', 'style': {'curve-style': 'bezier', 'target-arrow-shape': 'triangle'}}
                    ]
                ),
                html.Div(id='node-info', style={"marginTop": "10px", "whiteSpace": "pre-line"})
            ]
    )

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
        depth_map = refgraph.dm

        if not G or len(G.nodes) == 0:
            print("Graph is empty.")
            return []

        sorted_nodes = sorted(G.nodes(), key=lambda n: G.nodes[n].get('year', float('inf')))
        elements = []
        print(depth_map)
        for i, node in enumerate(sorted_nodes):
            print(node)
            meta = metadata.get(node, {})
            title = meta.get('title', node)
            year = meta.get('year', 'N/A')
            url = meta.get('url', 'N/A')
            citations = G.out_degree(node)

            label = (title[:60] + '...') if title and len(title) > 60 else (title or node)

            # X = depth level + small horizontal offset
            x = depth_map.get(node) * 3000 + (i % 3) * 500

            # Y = based on year (more recent = higher)
            y = -(year - 1950) * 100 if year else i * 600  # fallback if year missing


            elements.append({
                'data': {
                    'id': node,
                    'title': title,
                    'label': label,
                    'year': year,
                    'citations': citations,
                    'url': url
                },
                'position': {
                    'x': x,
                    'y': y
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
        return f"Title: {data.get('title', '')}\nYear: {data.get('year', 'N/A')}\nLink: {data.get('url')}"
    return "Hover over a node to see info."

if __name__ == '__main__':
    app.run_server(debug=True)