import requests
import urllib.parse
import json
import os
import uuid
import logging
from fusionauth.fusionauth_client import FusionAuthClient
from dotenv import load_dotenv

load_dotenv()

REGION_NAME = "us-west-2"

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
    
    def find_entity_by_agenttype(self, entity_agenttype_name):
        """
        Find an entity by type field in the data object and return its client_id
        """
        try:
            # Search entities by type using the search API
            search_request = {
                "search": {
                    "queryString": f"data.agenttype:{entity_agenttype_name}"
                }
            }
            
            # Use the generic request method for entity search
            response = self.client.search_entities(search_request)
            
            if response.was_successful():
                entities = response.success_response.get('entities', [])
                if entities:
                    # Return the client_id, systemprompt of the first matching entity
                    first_entity = entities[0]
                    model = None
                    if first_entity.get('data').get('model'):
                        model = first_entity.get('data').get('model')
                    return first_entity.get('clientId'), first_entity.get('data').get('systemprompt'), model
                else:
                    print(f"No entities found with type: {entity_agenttype_name}")
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


def invoke_agent(agent_arn, region, system_prompt, prompt, content, session_uuid, access_token, model):

    # print(f"Using Agent ARN from environment: {invoke_agent_arn}")

    # URL encode the agent ARN
    escaped_agent_arn = urllib.parse.quote(agent_arn, safe='')

    # Construct the URL
    url = f"https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{escaped_agent_arn}/invocations?qualifier=DEFAULT"

    trace_uuid = uuid.uuid4()

    # Set up headers
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Amzn-Trace-Id": str(trace_uuid), 
        "Content-Type": "application/json",
        "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id": str(session_uuid)
    }

    invoke_response = requests.post(
        url,
        headers=headers,
        data=json.dumps({"system_prompt": system_prompt, "prompt": prompt, "model": model})
    )

    # Print response in a safe manner
    #print(f"Status Code: {invoke_response.status_code}")
    #print(f"Response Headers: {dict(invoke_response.headers)}")
    
    # Handle response based on status code
    if invoke_response.status_code == 200:
        response_data = invoke_response.json()
        # print("Response JSON:")
        # print(json.dumps(response_data, indent=2))  
        result = response_data.get("result", {}).get("content", [{}])[0].get("text", "")
        return result
    elif invoke_response.status_code >= 400:
        print(f"Error Response ({invoke_response.status_code}):")
        error_data = invoke_response.json()
        print(json.dumps(error_data, indent=2))
    else:
        print(f"Unexpected status code: {invoke_response.status_code}")
        print("Response text:")
        print(invoke_response.text[:500])


def get_config(entity_agenttype):
   api_key = os.getenv('FUSIONAUTH_API_KEY')
   base_url = os.getenv('FUSIONAUTH_BASE_URL')
   supervisor_entity_id = os.getenv('SUPERVISOR_ENTITY_ID')
   
   if not api_key or not base_url or not supervisor_entity_id:
       print("Error: FUSIONAUTH_API_KEY, SUPERVISOR_ENTITY_ID, and FUSIONAUTH_BASE_URL must be set in .env file")
       exit(1)
   
   entity_manager = FusionAuthEntityManager(api_key, base_url)
   
   supervisor_client_id, supervisor_client_secret = entity_manager.retrieve_entity_by_id(supervisor_entity_id)
   
   if supervisor_client_id is None or supervisor_client_secret is None:
       print("Failed to retrieve client credentials from entity by ID")
       exit(1)
   
   client_id, system_prompt, model = entity_manager.find_entity_by_agenttype(entity_agenttype)
   
   if client_id is None or system_prompt is None:
       # model has a default
       print("Failed to obtain target client id or system prompt")
       exit(1)
   
   access_token = entity_manager.perform_client_credentials_grant(
           supervisor_client_id, 
           supervisor_client_secret, 
           scope='target-entity:'+client_id+':invoke'
       )
       
   if access_token is None:
       print("Failed to obtain access token")
       exit(1)
   return access_token, system_prompt, model

def handle_validation():
    validate_content_entity_type = 'validatecontent'

    access_token, validate_content_system_prompt, model = get_config(validate_content_entity_type)

    invoke_agent_arn = "arn:aws:bedrock-agentcore:us-west-2:011271748719:runtime/validateagent-dgzTssFW2J"
    
    content = "this is a blog post placeholder"
    with open('drafted.md', 'r') as file:
        content = file.read()
        #print(content)

    validate_check_prompt = "please validate this blog post from a technical point of view. please return the single string 'valid' if it is a valid blog post, or the single string 'invalid' if there are any technical errors or inconsistencies that would require rewriting. Please do not return any other text. ignore any typos or grammar errors in your evaluation.\n\n"+content

    rewrite_prompt = "please validate this blog post from a technical point of view. if it has incorrect statements, please rewrite it. Please return only the content, no preface or other commentary.\n\n"+content

    session_uuid = uuid.uuid4()

    # first validate the blog post, then rewrite if needed
    result_content = ""
    validate_result = invoke_agent(invoke_agent_arn, REGION_NAME, validate_content_system_prompt, validate_check_prompt, content, session_uuid, access_token, model)
    if validate_result != "valid":
        print("blog post had some invalid claims")
        rewrite_result = invoke_agent(invoke_agent_arn, REGION_NAME, validate_content_system_prompt, rewrite_prompt, content, session_uuid, access_token, model)
        result_content = rewrite_result
    else: 
        print("content looks valid")
        result_content = content

    if result_content:
        with open('validated.md', 'w') as file:
            file.write(result_content)


def handle_polishing():
    polish_content_entity_type = 'polishcontent'

    access_token, polish_content_system_prompt, model = get_config(polish_content_entity_type)

    invoke_agent_arn = "arn:aws:bedrock-agentcore:us-west-2:011271748719:runtime/polishagent-f55YTAHrt2"
    
    with open('validated.md', 'r') as file:
        content = file.read()
        #print(content)

    polish_prompt = "please polish this content to make sure it meets with the voice and content guidelines that FusionAuth upholds. You can find those here: https://github.com/FusionAuth/fusionauth-site/blob/main/DocsDevREADME.md . Please return just the content, not the outline or any other commentary.\n\n"+content

    session_uuid = uuid.uuid4()

    polished_result = invoke_agent(invoke_agent_arn, REGION_NAME, polish_content_system_prompt, polish_prompt, content, session_uuid, access_token, model)
    if polished_result:
        with open('polished.md', 'w') as file:
           file.write(polished_result)

def handle_drafting():
    draft_content_entity_type = 'draftcontent'

    access_token, draft_content_system_prompt, model = get_config(draft_content_entity_type)

    invoke_agent_arn = "arn:aws:bedrock-agentcore:us-west-2:011271748719:runtime/draftagent-3HGlni7thC"
    
    with open('outline.md', 'r') as file:
        content = file.read()

    write_prompt = "please write a blog post based on the following outline. Target 1500-3000 words. Please mimic the style found on https://fusionauth.io/blog, which is friendly and precise. The audience is engineering leaders. Please return just the content, not the outline or any other commentary.\n\n"+content

    session_uuid = uuid.uuid4()

    draft_result = invoke_agent(invoke_agent_arn, REGION_NAME, draft_content_system_prompt, write_prompt, content, session_uuid, access_token, model)
    if draft_result:
        with open('drafted.md', 'w') as file:
            file.write(draft_result)

def main():
   handle_drafting()
   handle_validation()
   handle_polishing()

if __name__ == "__main__":
    main()
