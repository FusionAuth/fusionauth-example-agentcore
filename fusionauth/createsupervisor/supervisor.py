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

# Create the Agent entity with the specified data field
supervisor_entity_id = str(uuid.uuid4())
supervisor_entity_request = {
    "entity": {
        "name": "Supervisor",
        "type": {
            "id": agent_entity_type_id
        }
    }
}
    
client_response = client.create_entity(supervisor_entity_request, supervisor_entity_id)
if client_response.was_successful():
    print("Supervisor entity created successfully:")
    print(client_response.success_response)
else:
    print("Failed to create entity: ")
    print(client_response.error_response)

# Function to search for entities by type in data field
def find_entities_by_data_type(target_type):
    """Find entities that have a specific type in their data field"""

    # Retrieve entities
    entities_response = client.search_entities({ "search": {"queryString": "data.type: "+target_type }})

    entities = []

    if entities_response.was_successful():
        entities = entities_response.success_response.get('entities', [])
    else:
        print(f"Failed to search for entities: {entities_response.error_response}")
    
    return entities

draft_entities = find_entities_by_data_type('draftcontent')
validate_entities = find_entities_by_data_type('validatecontent')
polish_entities = find_entities_by_data_type('polishcontent')

# Combine all found entities. you might want to filter this and only pick the first one of each type.
target_entities = draft_entities + validate_entities + polish_entities 

# Function to create grants with 'invoke' scope
def create_entity_grant(recipient_entity_id, target_entity_id):
    """Create a grant with 'invoke' scope from recipient to target entity"""
    
    grant_request = {
        "grant": {
            "recipientEntityId": recipient_entity_id,
            "permissions": ["invoke"]  # Grant with 'invoke' scope
        }
    }
    
    grant_response = client.upsert_entity_grant(target_entity_id, grant_request)
    
    if grant_response.was_successful():
        return True
    else:
        return False

# Create grants from the newly created entity to all found entities

if target_entities:
    print(f"\nCreating grants with 'invoke' scope from Supervisor entity to {len(target_entities)} target entities:")
    
    successful_grants = 0
    for target_entity in target_entities:
        target_id = target_entity.get('id')
        target_name = target_entity.get('name')
        
        if create_entity_grant(supervisor_entity_id, target_id):
            successful_grants += 1
    
    print(f"\nGrant creation summary: {successful_grants}/{len(target_entities)} grants created successfully")
else:
    print("\nNo entities found with types 'abc' or 'def' - no grants to create")

