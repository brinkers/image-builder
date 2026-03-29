import logging
import requests


class ImageBuilderClient:
    BASE = "https://console.redhat.com/api/image-builder/v1"

    def __init__(self, token_key=None):
        self.token_key = token_key
        self.logger = logging.getLogger(__name__)

    def _call_api(self, method: str, endpoint: str, **params): 
        headers = {"Content-Type": "application/json"}
        if self.token_key:
            headers.update({"Authorization": f"Bearer {self.token_key}"})
        self.logger.debug(f"Calling {method} {endpoint} with params {params}")
        response  = requests.request(method, f"{self.BASE}/{endpoint}", params=params, headers=headers)
        response.raise_for_status()
        return response.json()

    def _get(self, endpoint, **params):
        return self._call_api("GET", endpoint, **params)

    def _post(self, endpoint, **params):
        return self._call_api("POST", endpoint, **params)


    def get_something(self, query):
        data = self._get("search", q=query)
        return [{"title": r["title"], "url": r["url"]} for r in data["results"]]

    def get_version(self):
        return self._get("version")

    def get_readiness(self):
        return self._get("ready")

    def get_distributions(self):
        return self._get("distributions")
    
    def get_blueprints(self):
        return self._get("blueprints")
    
    def create_compose_from_blueprint(self, blueprint_id):
        return self._post(f"blueprints/{blueprint_id}/compose")

    def create_compose(self, name, distribution, data):
        payload = {
            "image_name": name,
            "distribution": distribution,
            "image_requests": [
                {
                    "architecture": "x86_64",
                    "image_type":  "vsphere",
                    "upload_request": {"type": "aws.s3", "options": {}},
                }
            ],
        }
        headers = {"Content-Type": "application/json"}
        if self.token_key:
            headers.update({"Authorization": f"Bearer {self.token_key}"})   
        resp = requests.post(f"{self.BASE}/compose", json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()


    def get_compose_status(self, compose_id):
        return self._get(f"composes/{compose_id}")
        