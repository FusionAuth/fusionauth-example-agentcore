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

# set up the new entity type
entity_type_id = uuid.uuid4()

entity_type_request = {
  "entityType": {
    "name": "Agent"
  }
}

client_response = client.create_entity_type(entity_type_request, entity_type_id)

if client_response.was_successful():
    print(client_response.success_response)
else:
    print(client_response.error_response)

invoke_permission_request = {
  "permission": {
    "description": "Ability to invoke this agent",
    "isDefault": True,
    "name": "invoke"
  }
}

client_response = client.create_entity_type_permission(entity_type_id, invoke_permission_request)

if client_response.was_successful():
    print("Success in creating entity type")
    print(client_response.success_response)
else:
    print(client_response.error_response)


# set up the lambda, assign to the tenant

lambda_body = """
function populate(jwt, recipientEntity, targetEntities, permissions) {
    // Set the client_id claim to the recipient entity's Id
    jwt.client_id = recipientEntity.id;
}
""".strip()

lambda_request = {
            "lambda": {
                "body": lambda_body,
                "debug": True,  # Enable debug logging for development
                "engineType": "GraalJS",
                "name": "add_client_id",
                "type": "ClientCredentialsJWTPopulate"
            }
        }

lambda_id = uuid.uuid4()
client_response = client.create_lambda(lambda_request, lambda_id)

if client_response.was_successful():
    print("Success in creating lambda")
    print(client_response.success_response)
else:
    print(client_response.error_response)


tenants = []
client_response = client.retrieve_tenants()
if client_response.was_successful():
    tenants = client_response.success_response.get('tenants', [])

    for tenant in tenants:
        tenant_id = tenant['id']
        tenant_request = {}
        tenant_request['oauthConfiguration'] = {}
        tenant_request['oauthConfiguration']['clientCredentialsAccessTokenPopulateLambdaId'] = str(lambda_id)
        update_response = client.patch_tenant(tenant_id, {"tenant": tenant_request})
    
        if client_response.was_successful():
            print("Success in updating tenant")
            print(update_response.success_response)
        else:
            print(update_response.error_response)
