To run the script:

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# update .env with your API key and FusionAuth location

python agents.py
