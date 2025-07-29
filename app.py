from dash import Dash, html, dcc, Output, Input, State # Dash imports
import dash_cytoscape as cyto
import networkx as nx
import sys
sys.path.append("./src")
from EuroPMCRefGraph import EuroPMCRefGraph as EuroPMC 

app = Dash(__name__)
cyto.load_extra_layouts()

def build_graph(keyword: str) -> nx.Graph:
    """
    Build the networkx graph
    Parameters:
        keyword (str): the keyword to build the graph around
    """
    obj = EuroPMC(keyword)
    G = obj.dg

    ### TODO: 
    # - Call function to scrape metadata and store it like below
    nx.set_node_attributes(G, {n: f"{keyword}_{n}" for n in G.nodes()}, "label")
    return G

def nx_to_cytoscape(G: nx.DiGraph):
    """
    Converts the networkx graph to cytoscape ready ds
    Parameters:
        G (nx.Graph): The graph
    """
    return (
        [
            {"data": {"id": str(n), "label": G.nodes[n].get("label", str(n))}}
            for n in G.nodes()
        ]
        + [
            {"data": {"source": str(u), "target": str(v)}}
            for u, v in G.edges()
        ]
    )

##########
# The Dash app layout
app.layout = html.Div([
    html.H1("RefGraph"),
    dcc.Input(id='keyword-input', type='text', placeholder='Enter keyword'),
    html.Button("Search", id='submit-button', n_clicks=0),
    html.Div(id='graph-title'),
    dcc.Loading(
        cyto.Cytoscape(
            id='citation-network',
            layout={'name': 'cola',
                    'animate': True},
            style={'width': '100%', 'height': '800px'},
            elements=[],
            stylesheet=[
                {
                    'selector': 'node',
                    'style': {
                        'label': 'data(label)',
                        'width': 30,
                        'height': 30,
                        'background-color': '#0074D9',
                        'color': 'black',
                        'text-valign': 'center',
                        'text-halign': 'center',
                    }
                },
                {
                    'selector': 'edge',
                    'style': {
                        'width': 2,
                        'line-color': '#888',
                        'target-arrow-color': '#888',
                        'target-arrow-shape': 'triangle',
                        'arrow-scale': 1.5,
                        'curve-style': 'bezier'  # allows arcs with arrowheads
                    }
                }
            ]
        )

    )
])

@app.callback(
    Output('citation-network', 'elements'),
    Output('graph-title', 'children'),
    Input('submit-button', 'n_clicks'),
    State('keyword-input', 'value'),
    prevent_initial_call=True,
)
def update_graph(n_clicks, keyword):
    """
    Callback function to update the graph when a keyword is entered and the submit button is clicked
    """
    if not keyword:
        return [], "Please enter a keyword."
    G = build_graph(keyword)
    return nx_to_cytoscape(G), f"Graph for '{keyword}'"

if __name__ == '__main__':
    app.run_server(debug=True)
