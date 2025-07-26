import os
import httpx

from dotenv import load_dotenv

load_dotenv()


class PaperlessNGXService:
    def __init__(self):
        self.base_url = os.getenv("BASE_URL")
        self.token = os.getenv("PAPERLESS_TOKEN")
        self.url = f"http://{os.getenv("BASE_URL")}/api/documents/?query=simba"
        self.headers = {"Authorization": f"Token {os.getenv("PAPERLESS_TOKEN")}"}

    def get_data(self):
        print(f"Getting data from: {self.url}")
        r = httpx.get(self.url, headers=self.headers)
        return r.json()["results"]
