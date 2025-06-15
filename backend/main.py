from fastapi import FastAPI, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from integrations.airtable import authorize_airtable, get_items_airtable, oauth2callback_airtable, get_airtable_credentials
from integrations.notion import authorize_notion, get_items_notion, oauth2callback_notion, get_notion_credentials
from integrations.hubspot import authorize_hubspot, get_items_hubspot, oauth2callback_hubspot, get_hubspot_credentials

app = FastAPI()

origins = [
    "http://localhost:3000",  # React or JS frontend address
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    """
    Root endpoint for health check.
    Returns:
        Dictionary with a ping-pong response.
    """
    return {"Ping": "Pong"}

# Airtable Endpoints
@app.post("/integrations/airtable/authorize")
async def authorize_airtable_integration(user_id: str = Form(...), org_id: str = Form(...)):
    """
    Initiates Airtable OAuth flow.
    Args:
        user_id: User identifier.
        org_id: Organization identifier.
    Returns:
        Authorization URL.
    """
    return await authorize_airtable(user_id, org_id)

@app.get("/integrations/airtable/oauth2callback")
async def oauth2callback_airtable_integration(request: Request):
    """
    Handles Airtable OAuth callback.
    Args:
        request: FastAPI Request object.
    Returns:
        HTMLResponse to close the window.
    """
    return await oauth2callback_airtable(request)

@app.post("/integrations/airtable/credentials")
async def get_airtable_credentials_integration(user_id: str = Form(...), org_id: str = Form(...)):
    """
    Retrieves Airtable credentials from Redis.
    Args:
        user_id: User identifier.
        org_id: Organization identifier.
    Returns:
        OAuth credentials.
    """
    return await get_airtable_credentials(user_id, org_id)

@app.post("/integrations/airtable/load")
async def get_airtable_items(credentials: str = Form(...)):
    """
    Fetches Airtable items using credentials.
    Args:
        credentials: JSON string of OAuth credentials.
    Returns:
        List of IntegrationItem objects.
    """
    return await get_items_airtable(credentials)

# Notion Endpoints
@app.post("/integrations/notion/authorize")
async def authorize_notion_integration(user_id: str = Form(...), org_id: str = Form(...)):
    """
    Initiates Notion OAuth flow.
    Args:
        user_id: User identifier.
        org_id: Organization identifier.
    Returns:
        Authorization URL.
    """
    return await authorize_notion(user_id, org_id)

@app.get("/integrations/notion/oauth2callback")
async def oauth2callback_notion_integration(request: Request):
    """
    Handles Notion OAuth callback.
    Args:
        request: FastAPI Request object.
    Returns:
        HTMLResponse to close the window.
    """
    return await oauth2callback_notion(request)

@app.post("/integrations/notion/credentials")
async def get_notion_credentials_integration(user_id: str = Form(...), org_id: str = Form(...)):
    """
    Retrieves Notion credentials from Redis.
    Args:
        user_id: User identifier.
        org_id: Organization identifier.
    Returns:
        OAuth credentials.
    """
    return await get_notion_credentials(user_id, org_id)

@app.post("/integrations/notion/load")
async def get_notion_items(credentials: str = Form(...)):
    """
    Fetches Notion items using credentials.
    Args:
        credentials: JSON string of OAuth credentials.
    Returns:
        List of IntegrationItem objects.
    """
    return await get_notion_items(credentials)

# HubSpot Endpoints
@app.post("/integrations/hubspot/authorize")
async def authorize_hubspot_integration(user_id: str = Form(...), org_id: str = Form(...)):
    """
    Initiates HubSpot OAuth flow.
    Args:
        user_id: User identifier.
        org_id: Organization identifier.
    Returns:
        Authorization URL.
    """
    return await authorize_hubspot(user_id, org_id)

@app.get("/integrations/hubspot/oauth2callback")
async def oauth2callback_hubspot_integration(request: Request):
    """
    Handles HubSpot OAuth callback.
    Args:
        request: FastAPI Request object.
    Returns:
        HTMLResponse to close the window.
    """
    return await oauth2callback_hubspot(request)

@app.post("/integrations/hubspot/credentials")
async def get_hubspot_credentials_integration(user_id: str = Form(...), org_id: str = Form(...)):
    """
    Retrieves HubSpot credentials from Redis.
    Args:
        user_id: User identifier.
        org_id: Organization identifier.
    Returns:
        OAuth credentials.
    """
    return await get_hubspot_credentials(user_id, org_id)

@app.post("/integrations/hubspot/load")
async def get_hubspot_items(credentials: str = Form(...)):
    """
    Fetches HubSpot items using credentials.
    Args:
        credentials: JSON string of OAuth credentials.
    Returns:
        List of IntegrationItem objects.
    """
    return await get_items_hubspot(credentials)