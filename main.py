import datetime
import logging
import os
from typing import Any, Union

import argparse
import chromadb
import ollama
from openai import OpenAI


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
parser.add_argument(
        "--index", help="index a file"
)

ppngx = PaperlessNGXService()

openai_client = OpenAI()

def index_using_pdf_llm():
    files = ppngx.get_data()
    for file in files:
        document_id = file["id"]
        pdf_path = ppngx.download_pdf_from_id(id=document_id)
        image_paths = pdf_to_image(filepath=pdf_path)
        print(f"summarizing {file}")
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
        print(docs[index]["original_file_name"])
        metadata = {
             "created_date": date_to_epoch(docs[index]["created_date"]),
             "filename": docs[index]["original_file_name"]
        }
        chunker.chunk_document(
            document=text,
            metadata=metadata,
        )

def chunk_text(texts: list[str], collection):
    chunker = Chunker(collection)

    for index, text in enumerate(texts):
        metadata = {}
        chunker.chunk_document(
            document=text,
            metadata=metadata,
        )

def consult_oracle(input: str, collection):
    print(input)
    import time
    start_time = time.time()

    # Ask
    # print("Starting query generation")
    # qg_start = time.time()
    # qg = QueryGenerator()
    # metadata_filter = qg.get_query(input)
    # qg_end = time.time()
    # print(f"Query generation took {qg_end - qg_start:.2f} seconds")
    # print(metadata_filter)

    print("Starting embedding generation")
    embedding_start = time.time()
    embeddings = Chunker.embedding_fx(input=[input])
    embedding_end = time.time()
    print(f"Embedding generation took {embedding_end - embedding_start:.2f} seconds")

    print("Starting collection query")
    query_start = time.time()
    results = collection.query(
        query_texts=[input],
        query_embeddings=embeddings,
        #where=metadata_filter,
    )
    print(results)
    query_end = time.time()
    print(f"Collection query took {query_end - query_start:.2f} seconds")

    # Generate
    print("Starting LLM generation")
    llm_start = time.time()
    # output = ollama.generate(
        # model="gemma3n:e4b",
        # prompt=f"You are a helpful assistant that understandings veterinary terms. Using the following data, help answer the user's query by providing as many details as possible.  Using this data: {results}. Respond to this prompt: {input}",
    # )
    response = openai_client.responses.create(
        model="gpt-4o-mini",
        input=f"You are a helpful assistant that understandings veterinary terms. Using the following data, help answer the user's query by providing as many details as possible.  Using this data: {results}. Respond to this prompt: {input}",
    )
    llm_end = time.time()
    print(f"LLM generation took {llm_end - llm_start:.2f} seconds")

    total_time = time.time() - start_time
    print(f"Total consult_oracle execution took {total_time:.2f} seconds")

    return response.output_text


def paperless_workflow(input):
    # Step 1: Get the text
    ppngx = PaperlessNGXService()
    docs = ppngx.get_data()

    chunk_data(docs, collection=simba_docs)
    consult_oracle(input, simba_docs)


def consult_simba_oracle(input: str):
    return consult_oracle(
        input=input,
        collection=simba_docs,
    )


if __name__ == "__main__":
    args = parser.parse_args()
    if args.reindex:
        print("Fetching documents from Paperless-NGX")
        ppngx = PaperlessNGXService()
        docs = ppngx.get_data()
        print(docs)
        print(f"Fetched {len(docs)} documents")
        #
        print("Chunking documents now ...")
        chunk_data(docs, collection=simba_docs)
        print("Done chunking documents")
        # index_using_pdf_llm()


    if args.index:
        with open(args.index) as file:
            extension = args.index.split(".")[-1]

            if extension == "pdf":
                pdf_path = ppngx.download_pdf_from_id(id=document_id)
                image_paths = pdf_to_image(filepath=pdf_path)
                print(f"summarizing {file}")
                generated_summary = summarize_pdf_image(filepaths=image_paths)
            elif extension in [".md", ".txt"]:
                chunk_text(texts=[file.readall()], collection=simba_docs)

    if args.query:
        print("Consulting oracle ...")
        print(consult_oracle(
            input=args.query,
            collection=simba_docs,
        ))
    else:
        print("please provide a query")


