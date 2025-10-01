#!/usr/bin/env python3
import sys
from dotenv import load_dotenv
import os
from fusionauth.fusionauth_client import FusionAuthClient

load_dotenv()

# Get API key and URL from environment variables
api_key = os.getenv('FUSIONAUTH_API_KEY')
base_url = os.getenv('FUSIONAUTH_BASE_URL')

if not api_key or not base_url:
    print("Error: FUSIONAUTH_API_KEY and FUSIONAUTH_BASE_URL must be set in .env file")
    exit(1)

client = FusionAuthClient(api_key, base_url)

if len(sys.argv) != 3:
    print('Usage: script.py <agent-type> <agent-arn>')
    sys.exit(1)

agent_type = sys.argv[1]
agent_arn = sys.argv[2]

# Search for entity
response = client.search_entities({'search': {'queryString': f'data.agenttype:{agent_type}'}})
entities = response.success_response['entities']

if not entities:
    print(f'No entity found with agenttype: {agent_type}')
    sys.exit(1)

entity = entities[0]
entity['data']['agentarn'] = agent_arn

# Update entity
client.update_entity(entity['id'], {'entity': entity})
print(f'Updated entity {entity["id"]}')
