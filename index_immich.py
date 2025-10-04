import httpx
import os
from pathlib import Path
import logging
import tempfile

from image_process import describe_simba_image
from request import PaperlessNGXService

logging.basicConfig(level=logging.INFO)


from dotenv import load_dotenv

load_dotenv()

# Configuration from environment variables
IMMICH_URL = os.getenv("IMMICH_URL", "http://localhost:2283")
API_KEY = os.getenv("IMMICH_API_KEY")
PERSON_NAME = os.getenv("PERSON_NAME", "Simba")  # Name of the tagged person/pet
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "./simba_photos")

# Set up headers
headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}


if __name__ == "__main__":
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
        if asset["type"] == "IMAGE":
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
    print(results.json()["assets"]["total"])
    for asset in results.json()["assets"]["items"]:
        if asset["type"] == "IMAGE":
            ids[asset["id"]] = asset.get("originalFileName")

    immich_asset_id = list(ids.keys())[1]
    immich_filename = ids.get(immich_asset_id)
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

    description_filepath = os.path.join("/Users/ryanchen/Programs/raggr", f"SIMBA_DESCRIBE_001.txt")
    file = open(description_filepath, "w+")
    file.write(image_description)
    file.close()

    file = open(description_filepath, 'rb')

    ppngx.upload_description(description_filepath=description_filepath, file=file, title="SIMBA_DESCRIBE_001.txt", exif_date=image_date)
    

    file.close()

    

    logging.info("Processing complete. Deleting file.")
    os.remove(file.name)
