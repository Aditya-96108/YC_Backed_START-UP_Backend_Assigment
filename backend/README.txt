```
VectorShift Integrations Technical Assessment - Backend Flow
=========================================================

This document outlines the setup and execution flow for the backend of the VectorShift Integrations Technical Assessment. The backend is built with Python and FastAPI, integrating with Airtable, Notion, and HubSpot via OAuth2, using Redis for temporary storage. Below are the locations to insert your credentials, installation steps, setup, and execution flow.

1. Inserting Credentials
-----------------------
Insert your OAuth2 credentials in the following files. I tested the integrations with my own credentials during development, which have been removed.

- HubSpot (Required per assessment):
  - File: backend/integrations/hubspot.py
  - Location:
    ```
    CLIENT_ID = "your_hubspot_client_id"  # Insert your HubSpot Client ID
    CLIENT_SECRET = "your_hubspot_client_secret"  # Insert your HubSpot Client Secret
    ```
  - Purpose: Authenticate OAuth flow to fetch contacts via /integrations/hubspot/load

- Airtable (Optional for testing):
  - File: backend/integrations/airtable.py
  - Location:
    ```
    CLIENT_ID = "your_airtable_client_id"  # Insert your Airtable Client ID
    CLIENT_SECRET = "your_airtable_client_secret"  # Insert your Airtable Client Secret
    ```
  - Purpose: Authenticate OAuth flow to fetch bases/tables via /integrations/airtable/load

- Notion (Optional for testing):
  - File: backend/integrations/notion.py
  - Location:
    ```
    CLIENT_ID = "your_notion_client_id"  # Insert your Notion Integration ID
    CLIENT_SECRET = "your_notion_client_secret"  # Insert your Notion Internal Integration Secret
    ```
  - Purpose: Authenticate OAuth flow to fetch pages/databases via /integrations/notion/load

- Redis:
  - No credentials required (connects to localhost:6379 by default).
  - Purpose: Store OAuth states and credentials temporarily (600s expiry).

2. Installations
----------------
- Python 3.8+: Ensure installed and added to PATH (download from https://www.python.org/downloads/ if needed).
- Redis: Run via Docker (recommended) or local installation.
  - Docker: `docker run -d -p 6379:6379 --name redis redis`
  - Local: Install Redis (e.g., `brew install redis` on macOS, `sudo apt install redis-server` on Linux).
- Python Packages: Install in a virtual environment:
```

python -m venv venv .\\venv\\Scripts\\activate # Windows source venv/bin/activate # macOS/Linux pip install fastapi httpx requests redis kombu uvicorn

```

3. Directory Structure
----------------------
```

backend/ ├── integrations/ │ ├── airtable.py │ ├── notion.py │ ├── hubspot.py │ ├── integration_item.py ├── redis_client.py ├── main.py ├── README.txt

```

4. Setup
--------
1. Insert your credentials in hubspot.py (required), and optionally in airtable.py, notion.py as specified above.
2. Ensure Redis is running:
   - Docker: `docker ps` to verify, `docker exec redis redis-cli ping` should return PONG.
   - Local: `redis-cli ping` should return PONG.
3. Place code files in the backend/ directory as shown above.

5. Execution Flow
----------------
1. Start the FastAPI server:
```

cd backend uvicorn main:app --host 127.0.0.1 --port 8000 --reload

```
2. Test the root endpoint:
```

curl http://localhost:8000/

```
Expected: {"Ping":"Pong"}
3. OAuth Flow (e.g., for HubSpot):
 - POST /integrations/hubspot/authorize with user_id, org_id (e.g., test_user, test_org):
   ```
   curl -X POST "http://localhost:8000/integrations/hubspot/authorize" -d "user_id=test_user&org_id=test_org"
   ```
   Returns an auth_url.
 - Open auth_url in a browser to authenticate.
 - Callback (/integrations/hubspot/oauth2callback) stores credentials in Redis and closes the window.
 - POST /integrations/hubspot/credentials to retrieve credentials:
   ```
   curl -X POST "http://localhost:8000/integrations/hubspot/credentials" -d "user_id=test_user&org_id=test_org"
   ```
 - POST /integrations/hubspot/load with credentials to fetch items:
   ```
   curl -X POST "http://localhost:8000/integrations/hubspot/load" -d "credentials={\"access_token\":\"your_token\"}"
   ```
   Items are printed to console and returned as IntegrationItem objects.
4. Repeat OAuth flow for Airtable (/integrations/airtable/*) and Notion (/integrations/notion/*) if testing.
5. Access Swagger UI at http://localhost:8000/docs for interactive testing.

6. Notes
--------
- HubSpot integration is fully implemented, fetching contacts as IntegrationItem objects per the assessment.
- Airtable and Notion integrations are provided as references; I fixed a bug in notion.py (get_items_notion return issue).
- Tested all integrations with my own credentials, removed for security.
- CORS is configured for a frontend at http://localhost:3000.
- For issues, check Redis connectivity (localhost:6379), port conflicts (8000), or credential validity.

Prepared by: Aditya Bidve
```