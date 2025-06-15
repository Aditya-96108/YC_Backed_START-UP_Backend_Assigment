import json
import secrets
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
import httpx
import asyncio
import base64
import requests
from integrations.integration_item import IntegrationItem
from redis_client import add_key_value_redis, get_value_redis, delete_key_redis

# Notion app credentials (replace with actual values for testing)
CLIENT_ID = "XXX"  # TODO: Replace with your Notion integration client ID
CLIENT_SECRET = "XXX"  # TODO: Replace with your Notion integration client secret
encoded_client_id_secret = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()

REDIRECT_URI = "http://localhost:8000/integrations/notion/oauth2callback"
authorization_url = f"https://api.notion.com/v1/oauth/authorize?client_id={CLIENT_ID}&response_type=code&owner=user&redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fintegrations%2Fnotion%2Foauth2callback"

async def authorize_notion(user_id: str, org_id: str) -> str:
    """
    Generates the Notion OAuth authorization URL and stores a secure state in Redis.
    Args:
        user_id: Unique identifier for the user.
        org_id: Unique identifier for the organization.
    Returns:
        Authorization URL for the user to authenticate with Notion.
    """
    state_data = {
        "state": secrets.token_urlsafe(32),  # Random state to prevent CSRF
        "user_id": user_id,
        "org_id": org_id
    }
    encoded_state = json.dumps(state_data)
    await add_key_value_redis(f"notion_state:{org_id}:{user_id}", encoded_state, expire=600)
    return f"{authorization_url}&state={encoded_state}"

async def oauth2callback_notion(request: Request):
    """
    Handles the Notion OAuth callback, validates the state, and exchanges the code for tokens.
    Args:
        request: FastAPI Request object containing query parameters.
    Returns:
        HTMLResponse to close the browser window after authentication.
    Raises:
        HTTPException: If state validation fails or token exchange fails.
    """
    if request.query_params.get("error"):
        raise HTTPException(status_code=400, detail=request.query_params.get("error"))
    
    code = request.query_params.get("code")
    encoded_state = request.query_params.get("state")
    state_data = json.loads(encoded_state)
    original_state = state_data.get("state")
    user_id = state_data.get("user_id")
    org_id = state_data.get("org_id")
    saved_state = await get_value_redis(f"notion_state:{org_id}:{user_id}")

    if not saved_state or original_state != json.loads(saved_state).get("state"):
        raise HTTPException(status_code=400, detail="State does not match.")

    async with httpx.AsyncClient() as client:
        response, _ = await asyncio.gather(
            client.post(
                "https://api.notion.com/v1/oauth/token",
                json={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": REDIRECT_URI
                },
                headers={
                    "Authorization": f"Basic {encoded_client_id_secret}",
                    "Content-Type": "application/json",
                }
            ),
            delete_key_redis(f"notion_state:{org_id}:{user_id}")
        )

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to exchange code for token")

    await add_key_value_redis(f"notion_credentials:{org_id}:{user_id}", json.dumps(response.json()), expire=600)
    
    close_window_script = """
    <html>
        <script>
            window.close();
        </script>
    </html>
    """
    return HTMLResponse(content=close_window_script)

async def get_notion_credentials(user_id: str, org_id: str) -> dict:
    """
    Retrieves Notion OAuth credentials from Redis and deletes them after use.
    Args:
        user_id: Unique identifier for the user.
        org_id: Unique identifier for the organization.
    Returns:
        Dictionary containing OAuth credentials.
    Raises:
        HTTPException: If no credentials are found in Redis.
    """
    credentials = await get_value_redis(f"notion_credentials:{org_id}:{user_id}")
    if not credentials:
        raise HTTPException(status_code=400, detail="No credentials found.")
    credentials = json.loads(credentials)
    if not credentials:
        raise HTTPException(status_code=400, detail="No credentials found.")
    await delete_key_redis(f"notion_credentials:{org_id}:{user_id}")
    return credentials

def _recursive_dict_search(data: dict, target_key: str) -> str | None:
    """
    Recursively searches for a key in a nested dictionary or list of dictionaries.
    Args:
        data: The dictionary or list to search.
        target_key: The key to find.
    Returns:
        The value of the target key if found, else None.
    """
    if target_key in data:
        return data[target_key]
    for value in data.values():
        if isinstance(value, dict):
            result = _recursive_dict_search(value, target_key)
            if result is not None:
                return result
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    result = _recursive_dict_search(item, target_key)
                    if result is not None:
                        return result
    return None

def create_integration_item_metadata_object(response_json: dict) -> IntegrationItem:
    """
    Creates an IntegrationItem object from a Notion API response.
    Args:
        response_json: The API response containing item metadata.
    Returns:
        IntegrationItem object with mapped fields.
    """
    name = _recursive_dict_search(response_json["properties"], "content")
    parent_type = "" if response_json["parent"]["type"] is None else response_json["parent"]["type"]
    parent_id = None if response_json["parent"]["type"] == "workspace" else response_json["parent"][parent_type]
    name = _recursive_dict_search(response_json, "content") if name is None else name
    name = "multi_select" if name is None else name
    name = f"{response_json['object']} {name}"

    integration_item_metadata = IntegrationItem(
        id=response_json["id"],
        type=response_json["object"],
        name=name,
        creation_time=response_json["created_time"],
        last_modified_time=response_json["last_edited_time"],
        parent_id=parent_id,
    )
    return integration_item_metadata

async def get_items_notion(credentials: str) -> list[IntegrationItem]:
    """
    Fetches items from Notion's search API and maps them to IntegrationItem objects.
    Args:
        credentials: JSON string containing OAuth credentials.
    Returns:
        List of IntegrationItem objects representing Notion pages or databases.
    Raises:
        HTTPException: If the API request fails.
    """
    credentials = json.loads(credentials)
    response = requests.post(
        "https://api.notion.com/v1/search",
        headers={
            "Authorization": f"Bearer {credentials.get('access_token')}",
            "Notion-Version": "2022-06-28",
        },
    )

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch Notion items")

    results = response.json().get("results", [])
    list_of_integration_item_metadata = []
    for result in results:
        list_of_integration_item_metadata.append(create_integration_item_metadata_object(result))
    
    print(f"Notion items: {list_of_integration_item_metadata}")
    return list_of_integration_item_metadata