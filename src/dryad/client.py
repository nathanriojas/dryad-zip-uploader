import requests


class DryadClient:
    def __init__(self, domain: str, client_id: str, client_secret: str):
        self.base_url = f"https://{domain}"
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None

    def authenticate(self) -> str:
        response = requests.post(
            f"{self.base_url}/oauth/token",
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials",
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
            },
            timeout=30,
        )
        response.raise_for_status()
        self.token = response.json()["access_token"]
        return self.token

    def test_connection(self):
        if not self.token:
            self.authenticate()

        response = requests.get(
            f"{self.base_url}/api/v2/test",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.token}",
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json()