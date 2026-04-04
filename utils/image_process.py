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
        img.save(new_filepath, "JPEG")
        logging.info("Extracting EXIF...")
        exif = {
            ExifTags.TAGS[k]: v for k, v in img.getexif().items() if k in ExifTags.TAGS
        }
        img = Image.open(new_filepath)
        input = new_filepath
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
        format=SimbaImageDescription.model_json_schema(),
    )

    result = SimbaImageDescription.model_validate_json(response["message"]["content"])

    return result


async def analyze_user_image(file_bytes: bytes) -> str:
    """Analyze an image uploaded by a user and return a text description.

    Uses llama-server (OpenAI-compatible API) with vision support.
    Falls back to OpenAI if llama-server is not configured.
    """
    import base64

    from openai import AsyncOpenAI

    llama_url = os.getenv("LLAMA_SERVER_URL")
    if llama_url:
        aclient = AsyncOpenAI(base_url=llama_url, api_key="not-needed")
        model = os.getenv("LLAMA_MODEL_NAME", "llama-3.1-8b-instruct")
    else:
        aclient = AsyncOpenAI()
        model = "gpt-4o-mini"

    b64 = base64.b64encode(file_bytes).decode("utf-8")

    response = await aclient.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful image analyst. Describe what you see in the image in detail. Be thorough but concise.",
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Please describe this image in detail."},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{b64}",
                        },
                    },
                ],
            },
        ],
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    args = parser.parse_args()
    if args.filepath:
        logging.info
        describe_simba_image(input=args.filepath)
