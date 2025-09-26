import requests
import urllib.parse
import json
import os
import uuid
import logging
from fusionauth.fusionauth_client import FusionAuthClient
from dotenv import load_dotenv

load_dotenv()

class FusionAuthEntityManager:
    def __init__(self, api_key, fusionauth_url):
        self.client = FusionAuthClient(api_key, fusionauth_url)
        self.base_url = fusionauth_url
    
    def retrieve_entity_by_id(self, entity_id):
        """
        Retrieve an entity by its ID and extract client_id and client_secret
        """
        try:
            # Use the direct API call since the Python client may not have a specific method
            response = self.client.retrieve_entity(entity_id)
            
            if response.was_successful():
                entity = response.success_response['entity']
                client_id = entity.get('clientId')
                client_secret = entity.get('clientSecret')
                return client_id, client_secret
            else:
                print(f"Error retrieving entity by ID: {response.error_response}")
                return None, None
        except Exception as e:
            print(f"Exception occurred: {e}")
            return None, None
    
    def find_entity_by_type(self, entity_type_name):
        """
        Find an entity by type field in the data object and return its client_id
        """
        try:
            # Search entities by type using the search API
            search_request = {
                "search": {
                    "queryString": f"data.type:{entity_type_name}"
                }
            }
            
            # Use the generic request method for entity search
            response = self.client.search_entities(search_request)
            
            if response.was_successful():
                entities = response.success_response.get('entities', [])
                if entities:
                    # Return the client_id of the first matching entity
                    first_entity = entities[0]
                    return first_entity.get('clientId')
                else:
                    print(f"No entities found with type: {entity_type_name}")
                    return None
            else:
                print(f"Error searching entities by type: {response.error_response}")
                return None
        except Exception as e:
            print(f"Exception occurred: {e}")
            return None
    
    def perform_client_credentials_grant(self, client_id, client_secret, scope='invoke'):
        """
        Perform a client credentials grant using the FusionAuth client library method
        """
        try:
            response = self.client.client_credentials_grant(
                client_id=client_id,
                client_secret=client_secret,
                scope=scope
            )
            
            if response.was_successful():
                token_data = response.success_response
                access_token = token_data.get('access_token')
                return access_token
            else:
                print(f"Error performing client credentials grant: {response.error_response}")
                return None
        except Exception as e:
            print(f"Exception occurred during client credentials grant: {e}")
            return None


api_key = os.getenv('FUSIONAUTH_API_KEY')
base_url = os.getenv('FUSIONAUTH_BASE_URL')
supervisor_entity_id = os.getenv('SUPERVISOR_ENTITY_ID')

if not api_key or not base_url or not supervisor_entity_id:
    print("Error: FUSIONAUTH_API_KEY, SUPERVISOR_ENTITY_ID, and FUSIONAUTH_BASE_URL must be set in .env file")
    exit(1)

entity_manager = FusionAuthEntityManager(api_key, base_url)

entity_id = supervisor_entity_id 
supervisor_client_id, supervisor_client_secret = entity_manager.retrieve_entity_by_id(entity_id)

if supervisor_client_id is None or supervisor_client_secret is None:
    print("Failed to retrieve client credentials from entity by ID")
    exit(1)

validate_content_entity_type = 'validatecontent'
validate_content_client_id = entity_manager.find_entity_by_type(validate_content_entity_type)

if validate_content_client_id is None:
    print("Failed to obtain target client id")
    exit(1)

access_token = entity_manager.perform_client_credentials_grant(
        supervisor_client_id, 
        supervisor_client_secret, 
        scope='target-entity:'+validate_content_client_id+':invoke'
    )
    
if access_token is None:
    print("Failed to obtain access token")
    exit(1)



# Configuration Constants
REGION_NAME = "us-west-2"

# === Agent Invocation Demo ===

## TODO need region name to be passed in
invoke_agent_arn = "arn:aws:bedrock-agentcore:us-west-2:011271748719:runtime/validateagent-dgzTssFW2J"

print(f"Using Agent ARN from environment: {invoke_agent_arn}")

# URL encode the agent ARN
escaped_agent_arn = urllib.parse.quote(invoke_agent_arn, safe='')

# Construct the URL
url = f"https://bedrock-agentcore.{REGION_NAME}.amazonaws.com/runtimes/{escaped_agent_arn}/invocations?qualifier=DEFAULT"

session_uuid = uuid.uuid4()
trace_uuid = uuid.uuid4()

# Set up headers
headers = {
    "Authorization": f"Bearer {access_token}",
    "X-Amzn-Trace-Id": str(trace_uuid), 
    "Content-Type": "application/json",
    "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id": str(session_uuid)
}

# Enable verbose logging for requests
#logging.basicConfig(level=logging.DEBUG)
#logging.getLogger("urllib3.connectionpool").setLevel(logging.DEBUG)

invoke_response = requests.post(
    url,
    headers=headers,
    data=json.dumps({"prompt": "please tell me what is the best way to integrate FusionAuth with an application written with rails?", "system_prompt":"You are a FusionAuth expert who knows OIDC in and out but not rails"})
)

# Print response in a safe manner
print(f"Status Code: {invoke_response.status_code}")
print(f"Response Headers: {dict(invoke_response.headers)}")

# Handle response based on status code
if invoke_response.status_code == 200:
    response_data = invoke_response.json()
    print("Response JSON:")
    print(json.dumps(response_data, indent=2))  
elif invoke_response.status_code >= 400:
    print(f"Error Response ({invoke_response.status_code}):")
    error_data = invoke_response.json()
    print(json.dumps(error_data, indent=2))
    
else:
    print(f"Unexpected status code: {invoke_response.status_code}")
    print("Response text:")
    print(invoke_response.text[:500])
