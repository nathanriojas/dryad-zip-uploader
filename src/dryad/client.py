import mimetypes
from pathlib import Path
from urllib.parse import quote
import time
import requests
from tqdm import tqdm


class ProgressFileReader:
    def __init__(self, file_obj, file_size: int, description: str):
        self.file_obj = file_obj
        self.progress = tqdm(
            total=file_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            desc=description,
        )

    def read(self, size=-1):
        chunk = self.file_obj.read(size)
        if chunk:
            self.progress.update(len(chunk))
        return chunk

    def close(self):
        self.progress.close()


class DryadClient:
    def __init__(self, domain: str, client_id: str, client_secret: str):
        self.base_url = f"https://{domain}"
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None

    def authenticate(self) -> str:
        max_auth_retries = 5
        retry_delay_seconds = 15

        for attempt in range(1, max_auth_retries + 1):
            response = requests.post(
                f"{self.base_url}/oauth/token",
                data={
                    "client_id": self.client_id.strip(),
                    "client_secret": self.client_secret.strip(),
                    "grant_type": "client_credentials",
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
                },
                timeout=30,
            )

            if response.ok:
                self.token = response.json()["access_token"]
                return self.token

            print(f"Dryad authentication failed on attempt {attempt}/{max_auth_retries}")
            print("Status:", response.status_code)
            print("Response body:")
            print(response.text)

            if attempt < max_auth_retries:
                print(f"Retrying authentication in {retry_delay_seconds} seconds...")
                time.sleep(retry_delay_seconds)

        response.raise_for_status()

    def _headers(self, content_type: str = "application/json") -> dict:
        if not self.token:
            self.authenticate()

        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": content_type,
            "Accept": "application/json",
        }

    def _encode_dataset_identifier(self, dataset_identifier: str) -> str:
        if "%" in dataset_identifier:
            return dataset_identifier
        return quote(dataset_identifier, safe="")

    def test_connection(self) -> dict:
        response = requests.get(
            f"{self.base_url}/api/v2/test",
            headers=self._headers(),
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def create_dataset(self, metadata: dict) -> dict:
        response = requests.post(
            f"{self.base_url}/api/v2/datasets",
            headers=self._headers(),
            json=metadata,
            timeout=30,
        )

        if not response.ok:
            print("Dryad create_dataset failed")
            print("Status:", response.status_code)
            print("Response body:")
            print(response.text)
            response.raise_for_status()

        return response.json()

    def list_files(self, dataset_identifier: str) -> list[dict]:
        dataset_identifier_encoded = self._encode_dataset_identifier(dataset_identifier)

        response = requests.get(
            f"{self.base_url}/api/v2/datasets/{dataset_identifier_encoded}/files",
            headers=self._headers(),
            timeout=30,
        )

        if not response.ok:
            return []

        data = response.json()

        if isinstance(data, list):
            return data

        if "_embedded" in data:
            for value in data["_embedded"].values():
                if isinstance(value, list):
                    return value

        return []

    def upload_file(
        self,
        dataset_identifier: str,
        file_path: str,
        description: str | None = None,
    ) -> dict:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        file_size = path.stat().st_size
        filename_encoded = quote(path.name, safe="")
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        dataset_identifier_encoded = self._encode_dataset_identifier(dataset_identifier)

        upload_url = (
            f"{self.base_url}/api/v2/datasets/"
            f"{dataset_identifier_encoded}/files/{filename_encoded}"
        )

        headers = self._headers(content_type=content_type)
        headers["Content-Length"] = str(file_size)

        if description:
            headers["Content-Description"] = description

        # print("Upload URL:", upload_url)

        with path.open("rb") as f:
            progress_file = ProgressFileReader(
                file_obj=f,
                file_size=file_size,
                description=f"Uploading {path.name}",
            )

            try:
                response = requests.put(
                    upload_url,
                    headers=headers,
                    data=progress_file,
                    timeout=None,
                )
            finally:
                progress_file.close()

        if not response.ok:
            print("Dryad upload_file failed")
            print("Status:", response.status_code)
            print("Response body:")
            print(response.text)
            response.raise_for_status()

        return response.json()