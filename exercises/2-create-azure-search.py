#!/usr/bin/env python
# coding: utf-8

# # 2. Generate your product search index
# 
# Run this notebook to automatically create a product search index from the data source provided, in the Azure AI Search service provisioned in the previous step. This notebook does the following:
# - looks for a **product catalog file in CSV format** at the named location.
# - creates an Azure AI Search client using the environment variables from the previous provisioning step
# - deletes pre-existing index for the given index name
# - creates index documents from product catalog file records using an OpenAI embeddings model
# - uploads the created documents to the given index name to recreate it
# 
# This notebook defines the following _helper methods_ to support this workflow:
# - `delete_index` - deletes the search index named in method argument.
# - `create_index_definition` - creates the search index named in method argument.
# - `gen_contoso_products` - creates vectorized index from data using OpenAI embeddings model
# 
# <br/>
# 
# ---

# In[1]:


# Step 1: Import dependencies, load environment variables
import os
import pandas as pd
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswParameters,
    HnswAlgorithmConfiguration,
    SemanticPrioritizedFields,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SemanticSearch,
    SemanticConfiguration,
    SemanticField,
    SimpleField,
    VectorSearch,
    VectorSearchAlgorithmKind,
    VectorSearchAlgorithmMetric,
    ExhaustiveKnnAlgorithmConfiguration,
    ExhaustiveKnnParameters,
    VectorSearchProfile,
)
from typing import List, Dict
from openai import AzureOpenAI

from pathlib import Path

from dotenv import load_dotenv
load_dotenv()


# In[2]:


# Step 2: Do a quick check that all required variables are set correctly.
#
# Local variables:
#   products_csv: path to the CSV file containing the product data
#.  product_index: name used for product index creation in Azure AI Search
#   api_version: hardcoded version for Azure OpenAI service configuration
#
# Environment variables:
#   CONTOSO_AI_SERVICES_ENDPOINT: env variable with Azure OpenAI endpoint
#   CONTOSO_AI_SERVICES_KEY: env variable with Azure OpenAI key
#   CONTOSO_SEARCH_SERVICES_ENDPOINT: env variable with Azure Search endpoint
#   CONTOSO_SEARCH_SERVICES_KEY: env variable with Azure Search key

product_csv = "../data/product_info/products.csv"
product_index = "contoso-products"
api_version = "2023-07-01-preview"
embeddings_model= "text-embedding-ada-002"

try:
    assert os.getenv("CONTOSO_AI_SERVICES_ENDPOINT"), "CONTOSO_AI_SERVICES_ENDPOINT is not set"
    assert os.getenv("CONTOSO_AI_SERVICES_KEY"), "CONTOSO_AI_SERVICES_KEY is not set"
    assert os.getenv("CONTOSO_SEARCH_ENDPOINT"), "CONTOSO_SEARCH_ENDPOINT is not set"
    assert os.getenv("CONTOSO_SEARCH_KEY"), "CONTOSO_SEARCH_KEY is not set"
    assert Path(product_csv).is_file(), "Product CSV file does not exist"
    assert product_index, "Product index name is not set"
    assert api_version, "API version is not set"
    assert embeddings_model, "Embeddings model is not set"
    print("✅ | Required environment and path variables are set correctly")
except AssertionError as e:
    print(f"🛑 | Assertion Error: {e}")


# In[3]:


# Method Definition: delete_index
#  Takes a search client and search index name as arguments
#  Uses search client to delete that search index if it exists
#
def delete_index(search_index_client: SearchIndexClient, search_index: str):
    print(f"deleting index {search_index}")
    search_index_client.delete_index(search_index)


# In[4]:


# Method Definition: create_index
#   Takes a search index name as argument
#   Creates the Azure AI Search index with that name (and returns it)
#
def create_index_definition(name: str) -> SearchIndex:
    """
    Returns an Azure Cognitive Search index with the given name.
    """

    # Create Azure AI Search "field" objects for fields we want to index. 
    # The "embedding" field is a vector field used for vector search.
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="content", type=SearchFieldDataType.String),
        SimpleField(name="filepath", type=SearchFieldDataType.String),
        SearchableField(name="title", type=SearchFieldDataType.String),
        SimpleField(name="url", type=SearchFieldDataType.String),
        SearchField(
            name="contentVector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=1536,  # Size of vector created by text-embedding-ada-002 model.
            vector_search_profile_name="myHnswProfile",
        ),
    ]

    # Create Azure AI Search "semantic configuration" for using Semantic Ranker capability
    # Prioritize the title and content fields for semantic ranking.
    semantic_config = SemanticConfiguration(
        name="default",
        prioritized_fields=SemanticPrioritizedFields(
            title_field=SemanticField(field_name="title"),
            keywords_fields=[],
            content_fields=[SemanticField(field_name="content")],
        ),
    )

    # Create an Azure AI Search "Semantic Search" instance with this configuration
    semantic_search = SemanticSearch(configurations=[semantic_config])

    # Create Azure AI Search configuration for using Vector Search capability
    # Define vector search using the HNSW (Hierarchical Navigable Small World) algorithm
    # This does approximate nearest neighbor search with cosine distance as similarity metric
    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(
                name="myHnsw",
                kind=VectorSearchAlgorithmKind.HNSW,
                parameters=HnswParameters(
                    m=4,
                    ef_construction=400,
                    ef_search=500,
                    metric=VectorSearchAlgorithmMetric.COSINE,
                ),
            ),
            ExhaustiveKnnAlgorithmConfiguration(
                name="myExhaustiveKnn",
                kind=VectorSearchAlgorithmKind.EXHAUSTIVE_KNN,
                parameters=ExhaustiveKnnParameters(
                    metric=VectorSearchAlgorithmMetric.COSINE
                ),
            ),
        ],
        profiles=[
            VectorSearchProfile(
                name="myHnswProfile",
                algorithm_configuration_name="myHnsw",
            ),
            VectorSearchProfile(
                name="myExhaustiveKnnProfile",
                algorithm_configuration_name="myExhaustiveKnn",
            ),
        ],
    )

    # Create the Azure AI Search "search index" with the requested name
    #  and configured using the fields, semantic ranking and vector search capabilties defined above.
    index = SearchIndex(
        name=name,
        fields=fields,
        semantic_search=semantic_search,
        vector_search=vector_search,
    )

    # Return the created index 
    return index


# In[5]:


# Method Definition: gen_contoso_products
#
# NN-TODO: Add detailed comments for learners
#
def gen_contoso_products(
    path: str,
) -> List[Dict[str, any]]:
    
    # We have already asserted that these variables are set correctly
    openai_service_endpoint = os.environ["CONTOSO_AI_SERVICES_ENDPOINT"]
    openai_service_key = os.environ["CONTOSO_AI_SERVICES_KEY"]
    openai_deployment = embeddings_model

    # openai.Embedding.create() -> client.embeddings.create()
    client = AzureOpenAI(
        api_version=api_version,
        azure_endpoint=openai_service_endpoint,
        azure_deployment=openai_deployment,
        api_key=openai_service_key,
    )

    products = pd.read_csv(path)
    items = []
    for product in products.to_dict("records"):
        content = product["description"]
        id = str(product["id"])
        title = product["name"]
        url = f"/products/{title.lower().replace(' ', '-')}"
        emb = client.embeddings.create(input=content, model=openai_deployment)
        rec = {
            "id": id,
            "content": content,
            "filepath": f"{title.lower().replace(' ', '-')}",
            "title": title,
            "url": url,
            "contentVector": emb.data[0].embedding,
        }
        items.append(rec)
        print(" ☑️ | Generated product index for ", title)
    return items


# In[6]:


#
# NN-TODO: Add detailed comments for learners
#
contoso_search = os.environ["CONTOSO_SEARCH_ENDPOINT"]
contoso_search_key = os.environ["CONTOSO_SEARCH_KEY"]
index_name = "contoso-products"

search_index_client = SearchIndexClient(
    contoso_search, AzureKeyCredential(contoso_search_key)
)

delete_index(search_index_client, index_name)
index = create_index_definition(index_name)
print(f"creating index {index_name}")
search_index_client.create_or_update_index(index)
print(f"index {index_name} created")


# In[7]:


#
# NN-TODO: Add detailed comments for learners
#
print(f"indexing documents")
docs = gen_contoso_products(product_csv)
# Upload our data to the index.
search_client = SearchClient(
    endpoint=contoso_search,
    index_name=index_name,
    credential=AzureKeyCredential(contoso_search_key),
)
print(f" ☑️ | Uploading {len(docs)} documents to index {index_name} ...")
ds = search_client.upload_documents(docs)
print("✅ | Product indexes uploaded to Azure AI Search!") 

