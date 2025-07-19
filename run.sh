# 1. Clone and setup
git clone <your-repo>
cd context7-agent
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env with your OpenAI key

# 3. Run
python -m src.cli
