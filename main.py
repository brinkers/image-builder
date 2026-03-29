
import logging
import time
import requests
import dotenv
import os
import json
import image_builder


logging.basicConfig(
    level=logging.INFO,  # Set minimum log level
    format="%(asctime)s - %(levelname)s - %(message)s",  # Include time, level, and message
    datefmt="%Y-%m-%d %H:%M:%S"  # Custom time format
)

logger = logging.getLogger(__name__)
logger.info("Starting the image builder script.")

dotenv.load_dotenv()
TOKEN = os.environ["TOKEN"]
if not TOKEN:
    raise ValueError("TOKEN environment variable is not set.")

logger.info("Successfully loaded the TOKEN from environment variables.")

url = "https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token"

payload = {
    "grant_type": "refresh_token",
    "client_id": "rhsm-api",
    "refresh_token": TOKEN,
}

response = requests.post(url, data=payload)
response.raise_for_status()  

access_token = response.json().get("access_token")
logger.info("Successfully obtained the access token.")

api_client = image_builder.ImageBuilderClient(token_key=access_token)

blueprints = api_client.get_blueprints()
    
logger.info("Retrieved blueprints.")

bp  = [bp for bp in blueprints["data"] if bp["name"] == "StandardImage"][0]

logger.info("Found the 'StandardImage' blueprint.")

compose = api_client.create_compose_from_blueprint(bp["id"])

id = compose[0]["id"]
logger.info(f"Started compose, ID: {id}")

status = api_client.get_compose_status(id)
logger.info(f"Initial compose status: {status['image_status']['status']}")


sleep_time = 30
while status['image_status']['status'] not in ["success", "failure"]:
    logger.info(f"Compose status: {status['image_status']['status']}. Checking again in {sleep_time} seconds...")
    time.sleep(sleep_time)
    status = api_client.get_compose_status(id)  
    
logger.info(f"Final compose status: {status['image_status']['status']}")

print(json.dumps(status, indent=4))
      



