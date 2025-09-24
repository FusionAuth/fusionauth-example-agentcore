To run the setup script:

source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# update .env with your API key and FusionAuth location

python setup.py
