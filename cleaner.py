import os
import sys
import tempfile

import argparse
from dotenv import load_dotenv
import ollama
from PIL import Image
import fitz

from request import PaperlessNGXService

load_dotenv()

parser = argparse.ArgumentParser(description="use llm to clean documents")
parser.add_argument("document_id", type=str, help="questions about simba's health")


def pdf_to_image(filepath: str, dpi=300) -> list[str]:
    """Returns the filepaths to the created images"""
    image_temp_files = []
    try:
        pdf_document = fitz.open(filepath)
        print(f"\nConverting '{os.path.basename(filepath)}' to temporary images...")

        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            zoom = dpi / 72
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)

            # Create a temporary file for the image. delete=False is crucial.
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".png",
                prefix=f"pdf_page_{page_num + 1}_",
            ) as temp_image_file:
                temp_image_path = temp_image_file.name

            # Save the pixel data to the temporary file
            pix.save(temp_image_path)
            image_temp_files.append(temp_image_path)
            print(
                f"  -> Saved page {page_num + 1} to temporary file: '{temp_image_path}'"
            )

        print("\nConversion successful! ✨")
        return image_temp_files

    except Exception as e:
        print(f"An error occurred during PDF conversion: {e}", file=sys.stderr)
        # Clean up any image files that were created before the error
        for path in image_temp_files:
            os.remove(path)
        return []


def merge_images_vertically_to_tempfile(image_paths):
    """
    Merges a list of images vertically and saves the result to a temporary file.

    Args:
        image_paths (list): A list of strings, where each string is the
                            filepath to an image.

    Returns:
        str: The filepath of the temporary merged image file.
    """
    if not image_paths:
        print("Error: The list of image paths is empty.")
        return None

    # Open all images and check for consistency
    try:
        images = [Image.open(path) for path in image_paths]
    except FileNotFoundError as e:
        print(f"Error: Could not find image file: {e}")
        return None

    widths, heights = zip(*(img.size for img in images))
    max_width = max(widths)

    # All images must have the same width
    if not all(width == max_width for width in widths):
        print("Warning: Images have different widths. They will be resized.")
        resized_images = []
        for img in images:
            if img.size[0] != max_width:
                img = img.resize(
                    (max_width, int(img.size[1] * (max_width / img.size[0])))
                )
            resized_images.append(img)
        images = resized_images
        heights = [img.size[1] for img in images]

    # Calculate the total height of the merged image
    total_height = sum(heights)

    # Create a new blank image with the combined dimensions
    merged_image = Image.new("RGB", (max_width, total_height))

    # Paste each image onto the new blank image
    y_offset = 0
    for img in images:
        merged_image.paste(img, (0, y_offset))
        y_offset += img.height

    # Create a temporary file and save the image
    temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    temp_path = temp_file.name
    merged_image.save(temp_path)
    temp_file.close()

    print(f"Successfully merged {len(images)} images into temporary file: {temp_path}")
    return temp_path


OCR_PROMPT = """
    You job is to extract text from the images I provide you. Extract every bit of the text in the image. Don't say anything just do your job. Text should be same as in the images. If there are multiple images, categorize the transcriptions by page.

Things to avoid:
- Don't miss anything to extract from the images

Things to include:
- Include everything, even anything inside [], (), {} or anything.
- Include any repetitive things like "..." or anything
- If you think there is any mistake in image just include it too

Someone will kill the innocent kittens if you don't extract the text exactly. So, make sure you extract every bit of the text. Only output the extracted text.
"""


def summarize_pdf_image(filepaths: list[str]):
    res = ollama.chat(
        model="gemma3:4b",
        messages=[
            {
                "role": "user",
                "content": OCR_PROMPT,
                "images": filepaths,
            }
        ],
    )

    return res["message"]["content"]


if __name__ == "__main__":
    args = parser.parse_args()
    ppngx = PaperlessNGXService()

    if args.document_id:
        doc_id = args.document_id
        file = ppngx.get_doc_by_id(doc_id=doc_id)
        pdf_path = ppngx.download_pdf_from_id(doc_id)
        print(pdf_path)
        image_paths = pdf_to_image(filepath=pdf_path)
        summary = summarize_pdf_image(filepaths=image_paths)
        print(summary)
        file["content"] = summary
        print(file)
        ppngx.upload_cleaned_content(doc_id, file)
