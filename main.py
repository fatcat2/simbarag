import datetime
import logging
import os
import sqlite3

import argparse
import chromadb
import ollama


from request import PaperlessNGXService
from chunker import Chunker
from cleaner import pdf_to_image, summarize_pdf_image
from llm import LLMClient
from query import QueryGenerator


from dotenv import load_dotenv

_dotenv_loaded = load_dotenv()

# Configure ollama client with URL from environment or default to localhost
ollama_client = ollama.Client(
    host=os.getenv("OLLAMA_URL", "http://localhost:11434"), timeout=10.0
)

client = chromadb.PersistentClient(path=os.getenv("CHROMADB_PATH", ""))
simba_docs = client.get_or_create_collection(name="simba_docs2")
feline_vet_lookup = client.get_or_create_collection(name="feline_vet_lookup")

parser = argparse.ArgumentParser(
    description="An LLM tool to query information about Simba <3"
)

parser.add_argument("query", type=str, help="questions about simba's health")
parser.add_argument(
    "--reindex", action="store_true", help="re-index the simba documents"
)
parser.add_argument("--index", help="index a file")

ppngx = PaperlessNGXService()

llm_client = LLMClient()


def index_using_pdf_llm(doctypes):
    logging.info("reindex data...")
    files = ppngx.get_data()
    for file in files:
        document_id: int = file["id"]
        pdf_path = ppngx.download_pdf_from_id(id=document_id)
        image_paths = pdf_to_image(filepath=pdf_path)
        logging.info(f"summarizing {file}")
        generated_summary = summarize_pdf_image(filepaths=image_paths)
        file["content"] = generated_summary

    chunk_data(files, simba_docs, doctypes=doctypes)


def date_to_epoch(date_str: str) -> float:
    split_date = date_str.split("-")
    date = datetime.datetime(
        int(split_date[0]),
        int(split_date[1]),
        int(split_date[2]),
        0,
        0,
        0,
    )

    return date.timestamp()


def chunk_data(docs, collection, doctypes):
    # Step 2: Create chunks
    chunker = Chunker(collection)

    logging.info(f"chunking {len(docs)} documents")
    texts: list[str] = [doc["content"] for doc in docs]
    with sqlite3.connect("database/visited.db") as conn:
        to_insert = []
        c = conn.cursor()
        for index, text in enumerate(texts):
            metadata = {
                "created_date": date_to_epoch(docs[index]["created_date"]),
                "filename": docs[index]["original_file_name"],
                "document_type": doctypes.get(docs[index]["document_type"], ""),
            }

            if doctypes:
                metadata["type"] = doctypes.get(docs[index]["document_type"])

            chunker.chunk_document(
                document=text,
                metadata=metadata,
            )
            to_insert.append((docs[index]["id"],))

        c.executemany(
            "INSERT INTO indexed_documents (paperless_id) values (?)", to_insert
        )
        conn.commit()


def chunk_text(texts: list[str], collection):
    chunker = Chunker(collection)

    for index, text in enumerate(texts):
        metadata = {}
        chunker.chunk_document(
            document=text,
            metadata=metadata,
        )


def consult_oracle(
    input: str,
    collection,
    transcript: str = "",
):
    import time

    chunker = Chunker(collection)

    start_time = time.time()

    # Ask
    logging.info("Starting query generation")
    qg_start = time.time()
    qg = QueryGenerator()
    doctype_query = qg.get_doctype_query(input=input)
    # metadata_filter = qg.get_query(input)
    metadata_filter = {**doctype_query}
    logging.info(metadata_filter)
    qg_end = time.time()
    logging.info(f"Query generation took {qg_end - qg_start:.2f} seconds")

    logging.info("Starting embedding generation")
    embedding_start = time.time()
    embeddings = chunker.embedding_fx(inputs=[input])
    embedding_end = time.time()
    logging.info(
        f"Embedding generation took {embedding_end - embedding_start:.2f} seconds"
    )

    logging.info("Starting collection query")
    query_start = time.time()
    results = collection.query(
        query_texts=[input],
        query_embeddings=embeddings,
        where=metadata_filter,
    )
    query_end = time.time()
    logging.info(f"Collection query took {query_end - query_start:.2f} seconds")

    # Generate
    logging.info("Starting LLM generation")
    llm_start = time.time()
    system_prompt = "You are a helpful assistant that understands veterinary terms."
    transcript_prompt = f"Here is the message transcript thus far {transcript}."
    prompt = f"""Using the following data, help answer the user's query by providing as many details as possible.
    Using this data: {results}. {transcript_prompt if len(transcript) > 0 else ""}
    Respond to this prompt: {input}"""
    output = llm_client.chat(prompt=prompt, system_prompt=system_prompt)
    llm_end = time.time()
    logging.info(f"LLM generation took {llm_end - llm_start:.2f} seconds")

    total_time = time.time() - start_time
    logging.info(f"Total consult_oracle execution took {total_time:.2f} seconds")

    return output


def paperless_workflow(input):
    # Step 1: Get the text
    ppngx = PaperlessNGXService()
    docs = ppngx.get_data()

    chunk_data(docs, collection=simba_docs)
    consult_oracle(input, simba_docs)


def consult_simba_oracle(input: str, transcript: str = ""):
    return consult_oracle(
        input=input,
        collection=simba_docs,
        transcript=transcript,
    )


def filter_indexed_files(docs):
    with sqlite3.connect("database/visited.db") as conn:
        c = conn.cursor()
        c.execute(
            "CREATE TABLE IF NOT EXISTS indexed_documents (id INTEGER PRIMARY KEY AUTOINCREMENT, paperless_id INTEGER)"
        )
        c.execute("SELECT paperless_id FROM indexed_documents")
        rows = c.fetchall()
        conn.commit()

    visited = {row[0] for row in rows}
    return [doc for doc in docs if doc["id"] not in visited]


if __name__ == "__main__":
    args = parser.parse_args()
    if args.reindex:
        with sqlite3.connect("database/visited.db") as conn:
            c = conn.cursor()
            c.execute("DELETE FROM indexed_documents")
            conn.commit()

        # Delete all documents from the collection
        all_docs = simba_docs.get()
        if all_docs["ids"]:
            simba_docs.delete(ids=all_docs["ids"])

        logging.info("Fetching documents from Paperless-NGX")
        ppngx = PaperlessNGXService()
        docs = ppngx.get_data()
        docs = filter_indexed_files(docs)
        logging.info(f"Fetched {len(docs)} documents")

        # Delete all chromadb data
        ids = simba_docs.get(ids=None, limit=None, offset=0)
        all_ids = ids["ids"]
        if len(all_ids) > 0:
            simba_docs.delete(ids=all_ids)

        # Chunk documents
        logging.info("Chunking documents now ...")
        tag_lookup = ppngx.get_tags()
        doctype_lookup = ppngx.get_doctypes()
        chunk_data(docs, collection=simba_docs, doctypes=doctype_lookup)
        logging.info("Done chunking documents")

    # if args.index:
    # with open(args.index) as file:
    #     extension = args.index.split(".")[-1]
    #     if extension == "pdf":
    #         pdf_path = ppngx.download_pdf_from_id(id=document_id)
    #         image_paths = pdf_to_image(filepath=pdf_path)
    #         print(f"summarizing {file}")
    #         generated_summary = summarize_pdf_image(filepaths=image_paths)
    #     elif extension in [".md", ".txt"]:
    #         chunk_text(texts=[file.readall()], collection=simba_docs)

    if args.query:
        logging.info("Consulting oracle ...")
        print(
            consult_oracle(
                input=args.query,
                collection=simba_docs,
            )
        )
    else:
        logging.info("please provide a query")
