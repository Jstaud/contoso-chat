#!/usr/bin/env python
# coding: utf-8

# # 1. Push the prompt flow to AI Studio

# In[1]:


# import required libraries
import os
from azure.ai.ml import MLClient
from azure.ai.ml.entities import WorkspaceConnection
# Import required libraries
from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential

# Import required libraries
from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential

try:
    credential = DefaultAzureCredential()
    # Check if given credential can get token successfully.
    credential.get_token("https://management.azure.com/.default")
except Exception as ex:
    # Fall back to InteractiveBrowserCredential in case DefaultAzureCredential not work
    credential = InteractiveBrowserCredential()


# In[2]:


config_path = "../config.json"
from promptflow.azure import PFClient
pf_azure_client = PFClient.from_config(credential=credential, path=config_path)


# In[3]:


# Create unique name for pf name with date time
import datetime
now = datetime.datetime.now()
pf_name = "contoso-chat-{}".format(now.strftime("%Y-%m-%d-%H-%M-%S"))


# In[4]:


# Runtime no longer needed (not in flow schema)
# load flow
flow = "../contoso-chat/"


# In[5]:


contoso_chat_flow = pf_azure_client.flows.create_or_update(
    flow=flow,
    display_name=pf_name,
    type="chat")
print("Creating prompt flow", contoso_chat_flow)


# # 2. Navigate to AI Studio to test and deploy the prompt flow
