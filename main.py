import ollama
import os
from uuid import uuid4, UUID

from request import PaperlessNGXService

from math import ceil

import chromadb

from chromadb.utils.embedding_functions.ollama_embedding_function import (
    OllamaEmbeddingFunction,
)

from dotenv import load_dotenv

client = chromadb.EphemeralClient()
collection = client.create_collection(name="docs")

load_dotenv()


class Chunk:
    def __init__(
        self,
        text: str,
        size: int,
        document_id: UUID,
        chunk_id: int,
        embedding,
    ):
        self.text = text
        self.size = size
        self.document_id = document_id
        self.chunk_id = chunk_id
        self.embedding = embedding


class Chunker:
    def __init__(self) -> None:
        self.embedding_fx = OllamaEmbeddingFunction(
            url=os.getenv("OLLAMA_URL", ""),
            model_name="mxbai-embed-large",
        )

        pass

    def chunk_document(self, document: str, chunk_size: int = 300) -> list[Chunk]:
        doc_uuid = uuid4()

        chunks = []
        num_chunks = ceil(len(document) / chunk_size)
        document_length = len(document)

        for i in range(num_chunks):
            curr_pos = i * num_chunks
            to_pos = (
                curr_pos + num_chunks
                if curr_pos + num_chunks < document_length
                else document_length
            )
            text_chunk = document[curr_pos:to_pos]

            embedding = self.embedding_fx([text_chunk])
            collection.add(
                ids=[str(doc_uuid) + ":" + str(i)],
                documents=[text_chunk],
                embeddings=embedding,
            )

        return chunks


embedding_fx = OllamaEmbeddingFunction(
    url=os.getenv("OLLAMA_URL", ""),
    model_name="mxbai-embed-large",
)

# Step 1: Get the text
ppngx = PaperlessNGXService()
docs = ppngx.get_data()
texts = [doc["content"] for doc in docs]

# Step 2: Create chunks
chunker = Chunker()

print(f"chunking {len(texts)} documents")
for text in texts:
    chunker.chunk_document(document=text)

# Ask
input = "How many teeth has Simba had removed? Who is his current vet?"
embeddings = embedding_fx(input=[input])
results = collection.query(query_texts=[input], query_embeddings=embeddings)
print(results)
# Generate
output = ollama.generate(
    model="gemma3n:e4b",
    prompt=f"Using this data: {results}. Respond to this prompt: {input}",
)

print(output["response"])
