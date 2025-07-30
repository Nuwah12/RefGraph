import pyalex
import time
import networkx as nx
from pyvis.network import Network
from typing import Tuple, Dict, List

class OpenAlexRefGraph():
    def __init__(self, seed, depth=3, delay=0.5, max_nodes=50):
        """
        Define an OpenAlex RefGraph
        Parameters:
            - seed (str / list of str): doi or list of dois to seed the graph with
            - depth (int): how many iterations of grapgh building to do
            - delay (int/double): time to sleep between OpenAlex api calls to avoid throttling
            - max_nodes(int): maximum number of nodes to be considered in final graph
        """
        self.refg = self.build_backward_graph(seed, max_depth=depth, delay=delay, max_nodes=max_nodes)

    def get_references(self, doi):
        work = pyalex.Works()[doi]
        references = work.get('referenced_works')
        return references

    def _retrieve_metadata(self, doi):
        work = pyalex.Works()[doi]
        return {
                'title': work.get('title'),
                'year': work.get('publication_year'),
                'authorships': work.get('authorships'),
                'journal': work.get('host_venue', {}).get('display_name'),
            }

    def get_metadata(self, G, delay) -> List[dict]:
        """
        Fetch metadata for the completed graph.
        Parameters:
            - G (nx.DiGraph): the graph
            - delay (int): delay api calls
        """
        metadata = {}
        for i in G.nodes:
            metadata[i] = self._retrieve_metadata(i)
            time.sleep(delay)
        return metadata

    def build_backward_graph(self, seed_doi, max_depth=3, delay=0.5, max_nodes=15) -> Tuple[nx.DiGraph, Dict[str, dict]]:
        """
        Build the graph
        """
        G = nx.DiGraph()
        visited = set()
        queue = [(seed_doi, 0)]
        metadata = {}
        
        while queue:
            doi, depth = queue.pop(0)
            if doi in visited or depth > max_depth:
                continue
            print(len(visited))
            if len(visited) >= max_nodes:
                break
            visited.add(doi)
    
            try:
                refs = self.get_references(doi)
            except Exception as e:
                print(f"Failed on {doi}: {e}")
                continue
    #
            for ref in refs:
                #print(ref)
                G.add_edge(doi, ref)
                #print(f"Edge added from {doi} to {ref}")
                queue.append((ref, depth + 1))
    
            time.sleep(delay)  # avoid rate limiting
        
        to_remove = [n for n in G.nodes if G.out_degree(n) == 0 and G.in_degree(n) == 1]
        G.remove_nodes_from(to_remove)

        return G, self.get_metadata(G, delay)
        


            