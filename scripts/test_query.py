#!/usr/bin/env python3
"""Test the query_vector_store function."""

import asyncio
import os

from dotenv import load_dotenv

from blueprints.rag.logic import query_vector_store

# Load .env from the root directory
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
env_path = os.path.join(root_dir, ".env")
load_dotenv(env_path)


async def test_query(query: str):
    """Test a query against the vector store."""
    print(f"Query: {query}\n")
    result, docs = await query_vector_store(query)
    print(f"Found {len(docs)} documents\n")
    print("Serialized result:")
    print(result)
    print("\n" + "=" * 80 + "\n")


async def main():
    queries = [
        "What is Simba's weight?",
        "What medications is Simba taking?",
        "Tell me about Simba's recent vet visits",
    ]

    for query in queries:
        await test_query(query)


if __name__ == "__main__":
    asyncio.run(main())
