import logging
import os
import sqlite3

import httpx
from dotenv import load_dotenv
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.image_process import describe_simba_image
from utils.request import PaperlessNGXService

logging.basicConfig(level=logging.INFO)


load_dotenv()

# Configuration from environment variables
IMMICH_URL = os.getenv("IMMICH_URL", "http://localhost:2283")
API_KEY = os.getenv("IMMICH_API_KEY")
PERSON_NAME = os.getenv("PERSON_NAME", "Simba")  # Name of the tagged person/pet
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "./simba_photos")

# Set up headers
headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}

VISITED = {}

if __name__ == "__main__":
    conn = sqlite3.connect("./database/visited.db")
    c = conn.cursor()
    c.execute("select immich_id from visited")
    rows = c.fetchall()
    for row in rows:
        VISITED.add(row[0])

    ppngx = PaperlessNGXService()
    people_url = f"{IMMICH_URL}/api/search/person?name=Simba"
    people = httpx.get(people_url, headers=headers).json()

    simba_id = people[0]["id"]

    ids = {}

    asset_search = f"{IMMICH_URL}/api/search/smart"
    request_body = {"query": "orange cat"}
    results = httpx.post(asset_search, headers=headers, json=request_body)

    assets = results.json()["assets"]
    for asset in assets["items"]:
        if asset["type"] == "IMAGE" and asset["id"] not in VISITED:
            ids[asset["id"]] = asset.get("originalFileName")
    nextPage = assets.get("nextPage")

    # while nextPage != None:
    # logging.info(f"next page: {nextPage}")
    # request_body["page"] = nextPage
    # results = httpx.post(asset_search, headers=headers, json=request_body)
    # assets = results.json()["assets"]

    # for asset in assets["items"]:
    # if asset["type"] == "IMAGE":
    # ids.add(asset['id'])

    # nextPage = assets.get("nextPage")

    asset_search = f"{IMMICH_URL}/api/search/smart"
    request_body = {"query": "simba"}
    results = httpx.post(asset_search, headers=headers, json=request_body)
    for asset in results.json()["assets"]["items"]:
        if asset["type"] == "IMAGE":
            ids[asset["id"]] = asset.get("originalFileName")

    for immich_asset_id, immich_filename in ids.items():
        try:
            response = httpx.get(
                f"{IMMICH_URL}/api/assets/{immich_asset_id}/original", headers=headers
            )

            path = os.path.join("/Users/ryanchen/Programs/raggr", immich_filename)
            file = open(path, "wb+")
            for chunk in response.iter_bytes(chunk_size=8192):
                file.write(chunk)

            logging.info("Processing image ...")
            description = describe_simba_image(path)

            image_description = description.description
            image_date = description.image_date

            description_filepath = os.path.join(
                "/Users/ryanchen/Programs/raggr", "SIMBA_DESCRIBE_001.txt"
            )
            file = open(description_filepath, "w+")
            file.write(image_description)
            file.close()

            file = open(description_filepath, "rb")
            ppngx.upload_description(
                description_filepath=description_filepath,
                file=file,
                title="SIMBA_DESCRIBE_001.txt",
                exif_date=image_date,
            )
            file.close()

            c.execute("INSERT INTO visited (immich_id) values (?)", (immich_asset_id,))
            conn.commit()
            logging.info("Processing complete. Deleting file.")
            os.remove(file.name)
        except Exception as e:
            logging.info(f"something went wrong for {immich_filename}")
            logging.info(e)

    conn.close()
