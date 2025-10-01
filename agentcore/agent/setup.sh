REGION=us-west-2
FUSIONAUTH_BASE=https://dan-agentcore.fusionauth.io/
SUPERVISOR_CLIENT_ID=1d650c1b-37ae-48f7-9488-6d84c1695665
DRAFT_CLIENT_ID=b0229f52-8d3e-4fe1-a248-da2b359a7ed4
VALIDATE_CLIENT_ID=49dc597c-10fe-487c-b904-c8576f4e4789
POLISH_CLIENT_ID=92740acc-c58a-49ea-b32e-17078d160278

# draft
agentcore configure --non-interactive \
                    --region $REGION \
                    --entrypoint agent.py \
                    --name draftagent \
                    --requirements-file requirements.txt \
                    --authorizer-config '{ "customJWTAuthorizer": { "discoveryUrl": "'$FUSIONAUTH_BASE'/.well-known/openid-configuration", "allowedClients": [ "'$SUPERVISOR_CLIENT_ID'" ], "allowedAudience": [ "'$DRAFT_CLIENT_ID'" ] }}' 
sleep 1;

# validate
agentcore configure --non-interactive \
                    --region $REGION \
                    --entrypoint agent.py \
                    --name validateagent \
                    --requirements-file requirements.txt \
                    --authorizer-config '{ "customJWTAuthorizer": { "discoveryUrl": "'$FUSIONAUTH_BASE'/.well-known/openid-configuration", "allowedClients": [ "'$SUPERVISOR_CLIENT_ID'" ], "allowedAudience": [ "'$VALIDATE_CLIENT_ID'" ] }}' 
sleep 1;

# polish
agentcore configure --non-interactive \
                    --region $REGION \
                    --entrypoint agent.py \
                    --name polishagent \
                    --requirements-file requirements.txt \
                    --authorizer-config '{ "customJWTAuthorizer": { "discoveryUrl": "'$FUSIONAUTH_BASE'/.well-known/openid-configuration", "allowedClients": [ "'$SUPERVISOR_CLIENT_ID'" ], "allowedAudience": [ "'$POLISH_CLIENT_ID'" ] }}' 

sleep 1;

agentcore launch --agent draftagent
sleep 1;
agentcore launch --agent validateagent
sleep 1;
agentcore launch --agent polishagent
sleep 1;

grep agent_arn .bedrock_agentcore.yaml
