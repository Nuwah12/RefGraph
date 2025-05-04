import requests
from xml.etree import ElementTree
import networkx as nx
import matplotlib.pyplot as plt
from pyvis.network import Network
from alive_progress import alive_bar

class EuroPMCRefGraph():
    def __init__(self, keyword, nPages=1):
        self.keyword = keyword
        self.n_pages = nPages

        pmids = []
        with alive_bar(self.n_pages, force_tty=True) as bar:
            for i in range(0, self.n_pages):
                res = self.get_papers(keyword, pages=i, perPage=100)
                pmids.append(res)
                bar()
            pmids = list(set(sum(pmids, [])))

        self.citation_dict = self.get_citation_dict(pmids)

        self.dg = nx.DiGraph(self.citation_dict)

        self.dg = self.remove_uninformative(self.dg)
        self.dg = self.remove_orphans(self.dg)

    def remove_uninformative(self, graph):
        nodes_to_remove = [node for node in graph.nodes() if graph.out_degree(node) == 0 and graph.in_degree(node) == 1]
        print(f"Removing {len(nodes_to_remove)} nodes")
        graph.remove_nodes_from(nodes_to_remove)
        return graph

    def remove_orphans(self, graph):
        nodes_to_remove = [node for node in graph.nodes() if graph.out_degree(node) == 0 and graph.in_degree(node) == 0]
        print(f"Removing {len(nodes_to_remove)} nodes")
        graph.remove_nodes_from(nodes_to_remove)
        return graph

    # Get the most cited paper in the graph
    def get_most_cited(self, g, n=0, all_counts=False):
        if all_counts:
            return sorted(list(dg.in_degree()), key=lambda x: x[1], reverse=True)
        if (isinstance(n, int)):
            if n == 0:
                return sorted(list(dg.in_degree()), key=lambda x: x[1], reverse=True)[0]
            else:
                return sorted(list(dg.in_degree()), key=lambda x: x[1], reverse=True)[n]
        elif (isinstance(n, list)):
            ret = []
            s = sorted(list(dg.in_degree()), key=lambda x: x[1], reverse=True)
            for i in n:
                ret.append(s[i])
            return ret
        
    def get_papers(self, keyword, pages=1, perPage=15):
        # Build the URL for the search endpoint with the keyword query.
        url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={keyword}&page={pages}&pageSize={perPage}&format=xml"

        # Get the XML response from Europe PMC.
        response = requests.get(url)

        # Parse the XML into an ElementTree.
        pmids = []
        tree = ElementTree.fromstring(response.content)
        for result in tree.findall('.//result'):
            pmid_elem = result.find('pmid')
            if pmid_elem is not None:
                pmids.append(pmid_elem.text)
        #print(pmids)
        hit_count_elem = tree.find('.//hitCount')
        #if hit_count_elem is not None:
        #    print("Total hits:", hit_count_elem.text)
        return pmids

    def get_citation_dict(self, pmids, pages=1, perPage=100):
        citation_dict = {}
        with alive_bar(len(pmids), force_tty=True) as bar:
            for i, pmid in enumerate(pmids):
                url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/MED/{pmid}/references?page={pages}&pageSize={perPage}&format=xml"
                response = requests.get(url)
                tree = ElementTree.fromstring(response.content)

                # List to hold PMIDs that the current paper cites.
                cited_pmids = []
                # The XML is assumed to have <reference> elements each containing a <pmid> element.
                for ref in tree.findall('.//reference'):
                    cited_pmid_elem = ref.find('id')
                    if cited_pmid_elem is not None:
                        cited_pmids.append(cited_pmid_elem.text)

                citation_dict[pmid] = cited_pmids
                bar()
        return citation_dict

    def remove_no_refs(self, citation_dict):
        return {key: value for key, value in citation_dict.items() if value}