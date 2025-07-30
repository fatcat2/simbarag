import logging

import argparse
import chromadb
import ollama


from request import PaperlessNGXService
from chunker import Chunker


from dotenv import load_dotenv

client = chromadb.PersistentClient(path="/Users/ryanchen/Programs/raggr/chromadb")
simba_docs = client.get_or_create_collection(name="simba_docs")
feline_vet_lookup = client.get_or_create_collection(name="feline_vet_lookup")

parser = argparse.ArgumentParser(
    description="An LLM tool to query information about Simba <3"
)

parser.add_argument("query", type=str, help="questions about simba's health")
parser.add_argument(
    "--reindex", action="store_true", help="re-index the simba documents"
)

load_dotenv()


def chunk_data(texts: list[str], collection):
    # Step 2: Create chunks
    chunker = Chunker(collection)

    print(f"chunking {len(texts)} documents")
    for text in texts[: len(texts) // 2]:
        chunker.chunk_document(document=text)


def consult_oracle(input: str, collection):
    # Ask
    embeddings = Chunker.embedding_fx(input=[input])
    results = collection.query(query_texts=[input], query_embeddings=embeddings)
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
    texts = [doc["content"] for doc in docs]

    chunk_data(texts, collection=simba_docs)
    consult_oracle(input, simba_docs)


if __name__ == "__main__":
    args = parser.parse_args()
    if args.reindex:
        logging.info(msg="Fetching documents from Paperless-NGX")
        ppngx = PaperlessNGXService()
        docs = ppngx.get_data()
        texts = [doc["content"] for doc in docs]
        logging.info(msg=f"Fetched {len(texts)} documents")

        logging.info(msg="Chunking documents now ...")
        chunk_data(texts, collection=simba_docs)
        logging.info(msg="Done chunking documents")

    if args.query:
        logging.info("Consulting oracle ...")
        consult_oracle(
            input=args.query,
            collection=simba_docs,
        )
    else:
        print("please provide a query")
