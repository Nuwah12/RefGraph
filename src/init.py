#!/usr/bin/env python
# coding: utf-8

# In[2]:


import requests
from xml.etree import ElementTree
import networkx as nx
import matplotlib.pyplot as plt
from pyvis.network import Network


# In[10]:


def print_element_tree(element, indent=""):
    """Recursively prints the element tree structure."""
    print(indent + "<" + element.tag + ">")
    if element.text and element.text.strip():
        print(indent + "  " + element.text.strip())
    for subelement in element:
        print_element_tree(subelement, indent + "  ")
    print(indent + "</" + element.tag + ">")
# Build the URL for the search endpoint with the keyword query.
keyword = "bioinformatics"
url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={keyword}&page=1&pageSize=100&format=xml"

# Get the XML response from Europe PMC.
response = requests.get(url)

# Parse the XML into an ElementTree.
pmids = []
tree = ElementTree.fromstring(response.content)
for result in tree.findall('.//result'):
    pmid_elem = result.find('pmid')
    if pmid_elem is not None:
        pmids.append(pmid_elem.text)
print(pmids)
hit_count_elem = tree.find('.//hitCount')
if hit_count_elem is not None:
    print("Total hits:", hit_count_elem.text)
len(pmids)


# In[72]:


tree = ElementTree.fromstring(requests.get('https://www.ebi.ac.uk/europepmc/webservices/test/rest/MED/39546379/references?page=1&pageSize=100&format=xml').content)
#print_element_tree(tree)
for ref in tree.findall('.//reference'):
    print(ref.find('id').text)
    cited_pmid_elem = ref.find('pmid')
cited_pmid_elem


# In[11]:


citation_dict = {}
for i, pmid in enumerate(pmids):
    print(i)
    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/MED/{pmid}/references?page=1&pageSize=100&format=xml"
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


# In[13]:


graph = nx.Graph(citation_dict)


# In[12]:


citation_dict


# In[14]:


# Create a PyVis network; set notebook=True if you're in a Jupyter notebook.
net = Network(height="750px", width="100%", directed=True)

# Load your networkx graph into PyVis.
net.from_nx(graph)

# Generate and open the interactive graph in a browser.
net.show("citation_graph.html")

