
import time
import requests
import dotenv
import os
import json
import image_builder

dotenv.load_dotenv()
TOKEN = os.environ["TOKEN"]
if not TOKEN:
    raise ValueError("TOKEN environment variable is not set.")


url = "https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token"

payload = {
    "grant_type": "refresh_token",
    "client_id": "rhsm-api",
    "refresh_token": TOKEN,
}

response = requests.post(url, data=payload)
response.raise_for_status()  

access_token = response.json().get("access_token")

api_client = image_builder.ImageBuilderClient(token_key=access_token)

blueprints = api_client.get_blueprints()

print(json.dumps(blueprints, indent=4))

bp  = [bp for bp in blueprints["data"] if bp["name"] == "StandardImage"][0]

print(json.dumps(bp, indent=4))

compose = api_client.create_compose_from_blueprint(bp["id"])

print(json.dumps(compose, indent=4))

id = compose[0]["id"]
print(f"Compose ID: {id}")

status = api_client.get_compose_status(id)
print(json.dumps(status, indent=4))

sleep_time = 30
while status['image_status']['status'] not in ["success", "failure"]:
    print(f"Compose status: {status['image_status']['status']}. Checking again in {sleep_time} seconds...")
    time.sleep(sleep_time)
    status = api_client.get_compose_status(id)  
    
print(f"Final compose status: {status['image_status']['status']}")

print(json.dumps(status, indent=4))
      



