## Setup
### 1. Clone Repository
git clone <repo-url>
### 2. Install Dependencies
pip install -r requirements.txt
### 3. Create .env
Copy `.env.example` into `.env`
Add your:
- AWS Access Key
- AWS Secret Key
- Lambda ARNs
### 4. Run Gateway Setup
cd gateway
python create_gateway_with_targets.py
### 5. Run Supervisor Agent
cd ../agent
python supervisor_agent.py