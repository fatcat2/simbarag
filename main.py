import datetime
import logging
import os
from typing import Any, Union

import argparse
import chromadb
import ollama


from request import PaperlessNGXService
from chunker import Chunker
from query import QueryGenerator
from cleaner import pdf_to_image, summarize_pdf_image

from dotenv import load_dotenv

load_dotenv()

client = chromadb.PersistentClient(path=os.getenv("CHROMADB_PATH", ""))
simba_docs = client.get_or_create_collection(name="simba_docs")
feline_vet_lookup = client.get_or_create_collection(name="feline_vet_lookup")

parser = argparse.ArgumentParser(
    description="An LLM tool to query information about Simba <3"
)

parser.add_argument("query", type=str, help="questions about simba's health")
parser.add_argument(
    "--reindex", action="store_true", help="re-index the simba documents"
)

ppngx = PaperlessNGXService()


def index_using_pdf_llm():
    files = ppngx.get_data()
    for file in files:
        document_id = file["id"]
        pdf_path = ppngx.download_pdf_from_id(id=document_id)
        image_paths = pdf_to_image(filepath=pdf_path)
        generated_summary = summarize_pdf_image(filepaths=image_paths)
        file["content"] = generated_summary

    chunk_data(files, simba_docs)


def date_to_epoch(date_str: str) -> float:
    split_date = date_str.split("-")
    print(split_date)
    date = datetime.datetime(
        int(split_date[0]),
        int(split_date[1]),
        int(split_date[2]),
        0,
        0,
        0,
    )

    return date.timestamp()


def chunk_data(docs: list[dict[str, Union[str, Any]]], collection):
    # Step 2: Create chunks
    chunker = Chunker(collection)

    print(f"chunking {len(docs)} documents")
    print(docs)
    texts: list[str] = [doc["content"] for doc in docs]
    for index, text in enumerate(texts):
        metadata = {
            "created_date": date_to_epoch(docs[index]["created_date"]),
        }
        chunker.chunk_document(
            document=text,
            metadata=metadata,
        )


def consult_oracle(input: str, collection):
    # Ask
    qg = QueryGenerator()
    metadata_filter = qg.get_query("input")
    print(metadata_filter)
    embeddings = Chunker.embedding_fx(input=[input])
    results = collection.query(
        query_texts=[input],
        query_embeddings=embeddings,
        where=metadata_filter,
    )

    print(results)

    # Generate
    output = ollama.generate(
        model="gemma3n:e4b",
        prompt=f"You are a helpful assistant that understandings veterinary terms. Using the following data, help answer the user's query by providing as many details as possible.  Using this data: {results}. Respond to this prompt: {input}",
    )

    print(output["response"])


def paperless_workflow(input):
    # Step 1: Get the text
    ppngx = PaperlessNGXService()
    docs = ppngx.get_data()

    chunk_data(docs, collection=simba_docs)
    consult_oracle(input, simba_docs)


if __name__ == "__main__":
    args = parser.parse_args()
    if args.reindex:
        # logging.info(msg="Fetching documents from Paperless-NGX")
        # ppngx = PaperlessNGXService()
        # docs = ppngx.get_data()
        # logging.info(msg=f"Fetched {len(docs)} documents")
        #
        # logging.info(msg="Chunking documents now ...")
        # chunk_data(docs, collection=simba_docs)
        # logging.info(msg="Done chunking documents")
        index_using_pdf_llm()

    if args.query:
        logging.info("Consulting oracle ...")
        consult_oracle(
            input=args.query,
            collection=simba_docs,
        )
    else:
        print("please provide a query")
