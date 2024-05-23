#!/usr/bin/env python
# coding: utf-8

# # 3. Generate your promptflow connections to Azure
# 
# This promptflow uses a Directed Acyclic Graph (DAG) with each node containing a specific tool or function that processes the data as it _flows through_. The Contoso Chat flow has five nodes as follows
#  - `question_embedding` - converts incoming text (question) into vectorized query (embedding)
#  - `retrieve_documentation` - this uses the vectorized query to retrieve matching documents (search)
#  - `customer_lookup` - this uses the incoming text (question) to lookup relevant customer records (orders)
#  - `customer_prompt` - this takes the search and lookup results to create an enhanced prompt from original question
#  - `llm_response` - chat completion model processes the prompt to return text response (returned to user)
# 
# For this to work, some nodes will need to "connect" to relevant Azure-hosted services for completing their tasks. This requires us to set up _named_ promptflow connections ahead of time, so we can simply reference them in the configuration of those nodes. These are the key named connections we create:
# - `aoai-connection` - used for the question_embedding (text embedding) and llm_response (chat completion) tasks
# - `contoso-search`- used for the retrieve_documentation task (search query)
# - `contoso-cosmos` - used for the customer_lookup task (database query)
# 
# Run this notebook to automatically create these connection objects based on predefined environment variables from the previous provisioning step.
# 
# <br/>
# 
# ---

# In[1]:


#
# NN-TODO: Replace all hardcoded elements with local variables we can assert at start
# NN-TODO: Add detailed comments for learners
#
import os
from pathlib import Path

from promptflow import PFClient
from promptflow.entities import (
    AzureOpenAIConnection,
    CustomConnection,
    CognitiveSearchConnection,
)
from dotenv import load_dotenv

load_dotenv()

pf = PFClient()


# In[2]:


# NN-TODO: Add section to assert that required environment and local variables are defined
# NN-TODO: Add detailed comments for learners
#


# In[3]:


# Create local Azure OpenAI Connection
#
# NN-TODO: Replace all hardcoded elements with local variables we can assert at start
# NN-TODO: Add detailed comments for learners
#
AOAI_KEY= os.environ["CONTOSO_AI_SERVICES_KEY"]
AOAI_ENDPOINT= os.environ["CONTOSO_AI_SERVICES_ENDPOINT"]
API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION") or "2024-03-01-preview"
connection = AzureOpenAIConnection(
    name="aoai-connection",
    api_key=AOAI_KEY,
    api_base=AOAI_ENDPOINT,
    api_type="azure",
    api_version=API_VERSION,
)

print(f"Creating connection {connection.name}...")
result = pf.connections.create_or_update(connection)
print(result)


# In[4]:


# Create the local contoso-cosmos connection
#
# NN-TODO: Replace all hardcoded elements with local variables we can assert at start
# NN-TODO: Add detailed comments for learners
#
COSMOS_ENDPOINT = os.environ["COSMOS_ENDPOINT"]
COSMOS_KEY = os.environ["COSMOS_KEY"]
connection = CustomConnection(
    name="contoso-cosmos",
    configs={
        "endpoint": COSMOS_ENDPOINT,
        "databaseId": "contoso-outdoor",
        "containerId": "customers",
    },
    secrets={"key": COSMOS_KEY},
)

print(f"Creating connection {connection.name}...")
result = pf.connections.create_or_update(connection)
print(result)


# In[5]:


# Create the local contoso-search connection
#
# NN-TODO: Replace all hardcoded elements with local variables we can assert at start
# NN-TODO: Add detailed comments for learners
#
SEARCH_ENDPOINT = os.environ["CONTOSO_SEARCH_ENDPOINT"]
SEARCH_KEY = os.environ["CONTOSO_SEARCH_KEY"]
API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION") or "2024-03-01-preview"
connection = CognitiveSearchConnection(
    name="contoso-search",
    api_key=SEARCH_KEY,
    api_base=SEARCH_ENDPOINT,
    api_version=API_VERSION,
)

print(f"Creating connection {connection.name}...")
result = pf.connections.create_or_update(connection)
print(result)


# In[6]:


# Use the pf tool inline to validate connections were created
# NN-TODO: Add detailed comments for learners
#
get_ipython().system('pf connection list')

