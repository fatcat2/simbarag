import os
from math import ceil
import re
from uuid import UUID, uuid4

from chromadb.utils.embedding_functions.ollama_embedding_function import (
    OllamaEmbeddingFunction,
)
from dotenv import load_dotenv


load_dotenv()


def remove_headers_footers(text, header_patterns=None, footer_patterns=None):
    if header_patterns is None:
        header_patterns = [r"^.*Header.*$"]
    if footer_patterns is None:
        footer_patterns = [r"^.*Footer.*$"]

    for pattern in header_patterns + footer_patterns:
        text = re.sub(pattern, "", text, flags=re.MULTILINE)

    return text.strip()


def remove_special_characters(text, special_chars=None):
    if special_chars is None:
        special_chars = r"[^A-Za-z0-9\s\.,;:\'\"\?\!\-]"

    text = re.sub(special_chars, "", text)
    return text.strip()


def remove_repeated_substrings(text, pattern=r"\.{2,}"):
    text = re.sub(pattern, ".", text)
    return text.strip()


def remove_extra_spaces(text):
    text = re.sub(r"\n\s*\n", "\n\n", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def preprocess_text(text):
    # Remove headers and footers
    text = remove_headers_footers(text)

    # Remove special characters
    text = remove_special_characters(text)

    # Remove repeated substrings like dots
    text = remove_repeated_substrings(text)

    # Remove extra spaces between lines and within lines
    text = remove_extra_spaces(text)

    # Additional cleaning steps can be added here

    return text.strip()


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
    embedding_fx = OllamaEmbeddingFunction(
        url=os.getenv("OLLAMA_URL", ""),
        model_name="mxbai-embed-large",
    )

    def __init__(self, collection) -> None:
        self.collection = collection

    def chunk_document(self, document: str, chunk_size: int = 1000) -> list[Chunk]:
        doc_uuid = uuid4()

        chunk_size = min(chunk_size, len(document))

        chunks = []
        num_chunks = ceil(len(document) / chunk_size)
        document_length = len(document)

        for i in range(num_chunks):
            curr_pos = i * num_chunks
            to_pos = (
                curr_pos + chunk_size
                if curr_pos + chunk_size < document_length
                else document_length
            )
            text_chunk = self.clean_document(document[curr_pos:to_pos])

            embedding = self.embedding_fx([text_chunk])
            self.collection.add(
                ids=[str(doc_uuid) + ":" + str(i)],
                documents=[text_chunk],
                embeddings=embedding,
            )

        return chunks

    def clean_document(self, document: str) -> str:
        """This function will remove information that is noise or already known.

        Example: We already know all the things in here are Simba-related, so we don't need things like
        "Sumamry of simba's visit"
        """

        document = document.replace("\\n", "")
        document = document.strip()

        return preprocess_text(document)
