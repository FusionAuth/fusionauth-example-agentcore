To run the update arn script:

python3 -m venv venv  

source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# update .env with your API key and FusionAuth location

python updatearn.py <clientid> <arn>

run this once for each agent to put the ARN into the entity's data field for the supervisor script to use
