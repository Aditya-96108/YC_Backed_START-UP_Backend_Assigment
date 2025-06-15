import json
import secrets
import base64
import httpx
import asyncio
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
from integrations.integration_item import IntegrationItem
from redis_client import add_key_value_redis, get_value_redis, delete_key_redis

# Replace with your HubSpot app credentials
CLIENT_ID = "your_hubspot_client_id"
CLIENT_SECRET = "your_hubspot_client_secret"
REDIRECT_URI = "http://localhost:8000/integrations/hubspot/oauth2callback"
AUTH_URL = f"https://app.hubspot.com/oauth/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}"

async def authorize_hubspot(user_id, org_id):
    """
    Generate HubSpot OAuth authorization URL and store state in Redis.
    """
    state_data = {
        "state": secrets.token_urlsafe(32),
        "user_id": user_id,
        "org_id": org_id
    }
    encoded_state = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()
    await add_key_value_redis(f"hubspot_state:{org_id}:{user_id}", json.dumps(state_data), expire=600)
    auth_url = f"{AUTH_URL}&state={encoded_state}&scope=crm.objects.contacts"
    return auth_url

async def oauth2callback_hubspot(request: Request):
    """
    Handle HubSpot OAuth callback, validate state, and exchange code for tokens.
    """
    if request.query_params.get("error"):
        raise HTTPException(status_code=400, detail=request.query_params.get("error_description"))
    code = request.query_params.get("code")
    encoded_state = request.query_params.get("state")
    state_data = json.loads(base64.urlsafe_b64decode(encoded_state).decode())
    saved_state = await get_value_redis(f"hubspot_state:{state_data['org_id']}:{state_data['user_id']}")
    
    if not saved_state or state_data.get("state") != json.loads(saved_state).get("state"):
        raise HTTPException(status_code=400, detail="State does not match.")
    
    async with httpx.AsyncClient() as client:
        response, _ = await asyncio.gather(
            client.post(
                "https://api.hubapi.com/oauth/v1/token",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": REDIRECT_URI,
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            ),
            delete_key_redis(f"hubspot_state:{state_data['org_id']}:{state_data['user_id']}")
        )
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to exchange code for token")
    
    await add_key_value_redis(
        f"hubspot_credentials:{state_data['org_id']}:{state_data['user_id']}",
        json.dumps(response.json()),
        expire=600
    )
    
    close_window_script = """
    <html>
        <script>
            window.close();
        </script>
    </html>
    """
    return HTMLResponse(content=close_window_script)

async def get_hubspot_credentials(user_id, org_id):
    """
    Retrieve HubSpot credentials from Redis and delete them after use.
    """
    credentials = await get_value_redis(f"hubspot_credentials:{org_id}:{user_id}")
    if not credentials:
        raise HTTPException(status_code=400, detail="No credentials found.")
    credentials = json.loads(credentials)
    await delete_key_redis(f"hubspot_credentials:{org_id}:{user_id}")
    return credentials

async def get_items_hubspot(credentials) -> list[IntegrationItem]:
    """
    Fetch contacts from HubSpot and map to IntegrationItem objects.
    """
    credentials = json.loads(credentials)
    access_token = credentials.get("access_token")
    url = "https://api.hubapi.com/crm/v3/objects/contacts"
    headers = {"Authorization": f"Bearer {access_token}"}
    items = []
    
    async with httpx.AsyncClient() as client:
        while url:
            response = await client.get(url, headers=headers)
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch HubSpot items")
            data = response.json()
            for item in data.get("results", []):
                properties = item.get("properties", {})
                items.append(IntegrationItem(
                    id=item.get("id"),
                    type="Contact",
                    name=properties.get("email", "Unknown Contact"),
                    creation_time=item.get("createdAt"),
                    last_modified_time=item.get("updatedAt"),
                    parent_id=None,
                    parent_path_or_name=None
                ))
            url = data.get("paging", {}).get("next", {}).get("link")
    
    print(f"HubSpot items: {items}")
    return items