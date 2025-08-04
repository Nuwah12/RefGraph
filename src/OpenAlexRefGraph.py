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
        self.refg, self.md, self.dm = self.build_backward_graph(seed, max_depth=depth, delay=delay, max_nodes=max_nodes)

    def get_references(self, id):
        try:
            work = pyalex.Works()[id]
            print(work)
        except Exception as e:
            print(f"Couldn't find references for {id}: {e}")
            return []
        references = work.get('referenced_works')
        return references

    def _retrieve_metadata(self, id):
        work = pyalex.Works()[id]
        return {
                'title': work.get('title'),
                'year': work.get('publication_year'),
                'authorships': work.get('authorships'),
                'url': work.get('doi')
            }

    def get_metadata(self, G, delay) -> Dict[str, dict]:
        metadata = {}
        for i in G.nodes:
            try:
                metadata[i] = self._retrieve_metadata(i)
            except Exception as e:
                print(f"Metadata fetch failed for {i}: {e}")
                metadata[i] = {}
            time.sleep(delay)
        return metadata

    def build_backward_graph(self, seed_doi, max_depth=3, delay=1.5, max_nodes=15) -> Tuple[nx.DiGraph, Dict[str, dict]]:
        """
        Build the graph
        """
        G = nx.DiGraph()
        visited = set()
        queue = [(seed_doi, 0)]
        metadata = {}
        depth_map = {}

        seed_year = self._retrieve_metadata(seed_doi).get('year')
        time.sleep(delay)
        
        while queue: # while the queue has items
            doi, depth = queue.pop(0) # pop from the front of the queue
            depth_map[doi] = depth
            if doi in visited or depth > max_depth: # if the paper is already in the visited set or we have gone beyond max depth we do not add this paper
                continue
            print(len(visited))
            if len(visited) >= max_nodes: # place a hard limit on the amount of content in the graph; might want to change this if theres a way to make this faster
                break
            visited.add(doi) # add the paper to the set
            
            try:
                refs = self.get_references(doi) # get all references for the current paper
            except Exception as e:
                print(f"Failed on {doi}: {e}")
                continue
    #
            for ref in refs: # loop through all references
                ref_id = ref.split('/')[-1]  # clean OpenAlex ID
                #print(ref)
                G.add_edge(doi, ref_id) # add an edge (which also implicitly adds a node for ref)
                #print(f"Edge added from {doi} to {ref}")
                queue.append((ref_id, depth + 1)) # add the ref to the queue at a new level
    
            time.sleep(delay)  # avoid rate limiting
        
        to_remove = [n for n in G.nodes if G.out_degree(n) == 0 and G.in_degree(n) == 1]
        G.remove_nodes_from(to_remove)
        
        metadata = self.get_metadata(G, delay)
        remove_nodes = []

        for node in G.nodes:
            if node == seed_doi:
                continue

            year = metadata.get(node, {}).get("year")
            depth = depth_map.get(node)

            # Skip if missing
            if year is None or depth is None:
                remove_nodes.append(node)
                continue  # don't proceed with comparison

            # Remove if too recent
            if year >= seed_year - (depth ** 2):
                remove_nodes.append(node)
                continue

            # Remove if isolated
            if G.in_degree(node) == 0 and G.out_degree(node) == 0:
                remove_nodes.append(node)

        G.remove_nodes_from(remove_nodes)

        for node in G.nodes:
            if node in metadata:
                G.nodes[node]['year'] = metadata[node].get('year')
                G.nodes[node]['url'] = metadata[node].get('url')
                G.nodes[node]['title'] = metadata[node].get('title')

        return G, metadata, depth_map
        


            