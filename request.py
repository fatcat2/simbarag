import os
import tempfile
import httpx

from dotenv import load_dotenv

load_dotenv()


class PaperlessNGXService:
    def __init__(self):
        self.base_url = os.getenv("BASE_URL")
        self.token = os.getenv("PAPERLESS_TOKEN")
        self.url = f"http://{os.getenv('BASE_URL')}/api/documents/?query=simba"
        self.headers = {"Authorization": f"Token {os.getenv('PAPERLESS_TOKEN')}"}

    def get_data(self):
        print(f"Getting data from: {self.url}")
        r = httpx.get(self.url, headers=self.headers)
        return r.json()["results"]

    def get_doc_by_id(self, doc_id: int):
        url = f"http://{os.getenv('BASE_URL')}/api/documents/{doc_id}/"
        r = httpx.get(url, headers=self.headers)
        return r.json()

    def download_pdf_from_id(self, id: int) -> str:
        download_url = f"http://{os.getenv('BASE_URL')}/api/documents/{id}/download/"
        response = httpx.get(
            download_url, headers=self.headers, follow_redirects=True, timeout=30
        )
        response.raise_for_status()
        # Use a temporary file for the downloaded PDF
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        temp_file.write(response.content)
        temp_file.close()
        temp_pdf_path = temp_file.name
        pdf_to_process = temp_pdf_path
        return pdf_to_process

    def upload_cleaned_content(self, document_id, data):
        PUTS_URL = f"http://{os.getenv('BASE_URL')}/api/documents/{document_id}/"
        r = httpx.put(PUTS_URL, headers=self.headers, data=data)
        r.raise_for_status()

    def upload_description(self, description_filepath, file, title, exif_date: str):
        POST_URL = f"http://{os.getenv('BASE_URL')}/api/documents/post_document/"
        files = {'document': ('description_filepath', file, 'application/txt')}
        data = {
                "title": title,
                "create": exif_date,
                "document_type": 3
                "tags": [7]
        }

        r= httpx.post(POST_URL, headers=self.headers, data=data, files=files)
        r.raise_for_status()


if __name__ == "__main__":
    pp = PaperlessNGXService()
    pp.get_data()
