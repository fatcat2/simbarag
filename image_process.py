from ollama import Client
import argparse
import os
import logging
from PIL import Image, ExifTags
from pillow_heif import register_heif_opener
from pydantic import BaseModel

from dotenv import load_dotenv

load_dotenv()

register_heif_opener()

logging.basicConfig(level=logging.INFO)


parser = argparse.ArgumentParser(
    prog="SimbaImageProcessor",
    description="What the program does",
    epilog="Text at the bottom of help",
)

parser.add_argument("filepath")

client = Client(host=os.getenv("OLLAMA_HOST", "http://localhost:11434"))

class SimbaImageDescription(BaseModel):
    image_date: str
    description: str

def describe_simba_image(input):
    logging.info("Opening image of Simba ...")
    if "heic" in input.lower() or "heif" in input.lower():
        new_filepath = input.split(".")[0] + ".jpg"
        img = Image.open(input)
        img.save(new_filepath, 'JPEG')
        logging.info("Extracting EXIF...")
        exif = {
            ExifTags.TAGS[k]: v for k, v in img.getexif().items() if k in ExifTags.TAGS
        }
        img = Image.open(new_filepath)
        input=new_filepath
    else:
        img = Image.open(input)

        logging.info("Extracting EXIF...")
        exif = {
            ExifTags.TAGS[k]: v for k, v in img.getexif().items() if k in ExifTags.TAGS
        }

    if "MakerNote" in exif:
        exif.pop("MakerNote")

    logging.info(exif)

    prompt = f"Simba is an orange cat belonging to Ryan Chen. In 2025, they lived in New York. In 2024, they lived in California. Analyze the following image and tell me what Simba seems to be doing. Be extremely descriptive about Simba, things in the background, and the setting of the image. I will also include the EXIF data of the image, please use it to help you determine information about Simba. EXIF: {exif}. Put the notes in the description field and the date in the image_date field."

    logging.info("Sending info to Ollama ...")
    response = client.chat(
        model="gemma3:4b",
        messages=[
            {
                "role": "system",
                "content": "you are a very shrewd and descriptive note taker. all of your responses will be formatted like notes in bullet points. be very descriptive. do not leave a single thing out.",
            },
            {"role": "user", "content": prompt, "images": [input]},
        ],
        format=SimbaImageDescription.model_json_schema()
    )

    result = SimbaImageDescription.model_validate_json(response["message"]["content"])

    return result


if __name__ == "__main__":
    args = parser.parse_args()
    if args.filepath:
        logging.info
        describe_simba_image(input=args.filepath)
