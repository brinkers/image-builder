import json
import logging
import requests

BASE = "https://console.redhat.com/api/image-builder/v1"
TOKEN_URL = "https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token"


def _debug_request(r, *args, **kwargs):
    req = r.request

    print("\n=== REQUEST ===")
    print(f"{req.method} {req.url}")

    print("\nHeaders:")
    for k, v in req.headers.items():
        if k.lower() == "authorization":
            print(f"  {k}: <redacted>")
        else:
            print(f"  {k}: {v}")

    print("\nBody:")
    if req.body:
        try:
            print(json.dumps(json.loads(req.body), indent=2))
        except Exception:
            print(req.body)
    else:
        print("  <empty>")

    print("\n=== RESPONSE ===")
    print(f"Status: {r.status_code}")

    print("\nHeaders:")
    for k, v in r.headers.items():
        print(f"  {k}: {v}")

    print("\nBody:")
    try:
        print(json.dumps(r.json(), indent=2))
    except Exception:
        print(r.text)
    print("================\n")




class ImageBuilderClient:
    def __init__(self, client_id, client_secret, dumpResponse=False):
        self.logger = logging.getLogger(__name__)
        self.client_id = client_id
        self.client_secret = client_secret
        self.dumpResponse = dumpResponse
        self.access_token = self._get_token()


    def _get_token(self):
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "openid api.iam.service_accounts"
        }
        headers = {
            "content-type": "application/x-www-form-urlencoded"
        }

        response = requests.post(TOKEN_URL, data=payload, headers=headers)
        self.logger.debug(f"Token response: {response.status_code} {response.text}")
        response.raise_for_status()
        access_token = response.json().get("access_token")
        if access_token:
            self.logger.info(f"Obtained access token")
        else: 
            self.logger.error(f"Failed to obtain access token: {response.text}")
        return access_token
    

    def _call_api(self, method: str, endpoint: str, data=None): 
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers.update({"Authorization": f"Bearer {self.access_token}"})
        hooks = {"response": _debug_request} if self.dumpResponse else None

        self.logger.debug(f"Calling {method} {endpoint} with data {data}")
        response  = requests.request(method, f"{BASE}/{endpoint}", json=data, headers=headers, hooks=hooks)
        if response.status_code == 401:
            self.logger.info("Access token expired, refreshing...")
            self.access_token = self._get_token()
            headers.update({"Authorization": f"Bearer {self.access_token}"})
            response  = requests.request(method, f"{BASE}/{endpoint}", json=data, headers=headers, hooks=hooks) 

        response.raise_for_status()

        if not response.content or response.content.strip() == b"":
            return None

        return response.json()

    
    def _get(self, endpoint, data=None):
        return self._call_api("GET", endpoint, data=data)

    def _post(self, endpoint, data=None):
        return self._call_api("POST", endpoint, data=data )
    
    def _delete(self, endpoint):
        return self._call_api("DELETE", endpoint, data=None)

    def enable_http_debug(self):
        self.dumpResponse = True

    def disable_http_debug(self):
        self.dumpResponse = False

    def create_compose(self, payload):
        response = self._post(f"compose", data=payload)
        if response and "id" in response:
            return response['id']
        return None

    def get_composes(self):
        return self._get("composes")
        
    def delete_compose(self, compose_id):
        return self._delete(f"composes/{compose_id}")

    def get_compose_status(self, compose_id):
        return self._get(f"composes/{compose_id}")
        