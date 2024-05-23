#!/usr/bin/env python
# coding: utf-8

# # 1. Populate Customer Data in Azure Cosmos DB

# In[1]:


# Step 1: Import dependencies, load environment variables

from azure.cosmos import CosmosClient, exceptions, PartitionKey
import os

from dotenv import load_dotenv
load_dotenv()


# In[2]:


# Step 2: Validate that required environment variables are defined
# This requires the following properties to be defined.
#         key = to authenticate with your Azure CosmosDB account 
#    endpoint = to make requests to your Azure CosmosDB instance
#    database = the namespace for Contoso Chat app containers
#   container = the container storing your customer data

# The database and container names are hardcoded (for now)
# These names will also be used in setting up promptflow connections later
# NN-TODO:  Create environment variables for consistency and reuse 
DATABASE_NAME = 'contoso-outdoor'
CONTAINER_NAME = 'customers'

# The key and endpoint are set by the Azure provisioning step in .env
# Just read the values in and create a local CosmosClient instance.
COSMOS_ENDPOINT = os.environ["COSMOS_ENDPOINT"]
COSMOS_KEY =  os.environ["COSMOS_KEY"]
client = CosmosClient(COSMOS_ENDPOINT, credential=COSMOS_KEY)
print("✅ | Azure Cosmos DB client configured successfully")


# In[3]:


# Step 3: Check if the specified CosmosDB service contains the required database 
#         Else create it
client = CosmosClient(COSMOS_ENDPOINT, credential=COSMOS_KEY)
try:
    database = client.create_database(DATABASE_NAME)
    print("✅ | Azure Cosmos DB database CREATED: ",database.id.title())        
except exceptions.CosmosResourceExistsError:
    database = client.get_database_client(DATABASE_NAME)
    print("✅ | Azure Cosmos DB database exists: ",database.id.title())        


# In[4]:


# Step 4: Check if the database contains the required container
#         Else create it
try:
    container = database.create_container(id=CONTAINER_NAME, partition_key=PartitionKey(path="/id"))
    print("✅ | Azure Cosmos DB container CREATED: ",container.id.title())   
except exceptions.CosmosResourceExistsError:
    container = database.get_container_client(CONTAINER_NAME)
    print("✅ | Azure Cosmos DB container exists: ",container.id.title())   
except exceptions.CosmosHttpResponseError:
    raise


# In[5]:


# Step 5: Read customer data records from the specified folder (should be JSON files)
#         Iterate through JSON files in the folder (each representing a customer record)
#         Upsert each record into the CosmosDB container
import os
import json
import glob
path = '../data/customer_info'
 
for filename in glob.glob(os.path.join(path, '*.json')):
    with open(filename) as file:
        customer = json.load(file)
        container.upsert_item(customer)
        print('Upserted item with id: {0}'.format(customer['id']))

print("✅ | Updated Azure Cosmos DB container from data in: ",path)  


# In[6]:


# Step 6: Retrieve and list container items to validate data was inserted correctly
items = list(container.read_all_items(max_item_count=10))
print("✅ | Printing the ",len(items),"items from container for validation")  
for item in items:
    print(item)

