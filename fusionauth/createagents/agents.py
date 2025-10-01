from fusionauth.fusionauth_client import FusionAuthClient
import uuid
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API key and URL from environment variables
api_key = os.getenv('FUSIONAUTH_API_KEY')
base_url = os.getenv('FUSIONAUTH_BASE_URL')

if not api_key or not base_url:
    print("Error: FUSIONAUTH_API_KEY and FUSIONAUTH_BASE_URL must be set in .env file")
    exit(1)

client = FusionAuthClient(api_key, base_url)

def create_agent_entity(name, data):
    # Create the Agent entity with the specified data field
    entity_id = uuid.uuid4()
    entity_request = {
        "entity": {
            "name": name,
            "type": {
                "id": agent_entity_type_id
            },
            "data": data
        }
    }
    
    client_response = client.create_entity(entity_request, entity_id)
    if client_response.was_successful():
        print("Agent entity created successfully:")
        print(client_response.success_response)
    else:
        print("Failed to create Agent " + name + " entity: ")
        print(client_response.error_response)

# First, retrieve the existing Agent entity type ID
# (Assuming the Agent entity type was already created from your example script)
entity_types_response = client.retrieve_entity_types()
agent_entity_type_id = None

if entity_types_response.was_successful():
    entity_types = entity_types_response.success_response.get('entityTypes', [])
    for entity_type in entity_types:
        if entity_type.get('name') == 'Agent':
            agent_entity_type_id = entity_type.get('id')
            break
    
    if agent_entity_type_id:
        print(f"Found Agent entity type with ID: {agent_entity_type_id}")
    else:
        print("Agent entity type not found. Please run the entity type creation script first.")
        exit(1)
else:
    print("Failed to retrieve entity types:")
    print(entity_types_response.error_response)
    exit(1)

# enabled models can be found in the Bedrock Console

draft_content_data = {
    "agenttype": "draftcontent",
    "systemprompt": "You are a content expert who knows FusionAuth inside and outside. You follow the FusionAuth brand guidelines.",
    "model": "deepseek.v3-v1:0"
}
validate_content_data = {
    "agenttype": "validatecontent",
    "systemprompt": "You are a technical expert who knows FusionAuth very well, and has implemented it multiple times. You are extremely detail oriented and will flag any technical errors you see with content."
}
polish_content_data = {
    "agenttype": "polishcontent",
    "systemprompt": "You are a content expert who has written many highly rated technical articles. You follow the FusionAuth brand guidelines.",
    "model": "meta.llama3-3-70b-instruct-v1:0"
}
create_agent_entity("Draft Agent", draft_content_data);
create_agent_entity("Validate Agent", validate_content_data);
create_agent_entity("Polish Agent", polish_content_data);

