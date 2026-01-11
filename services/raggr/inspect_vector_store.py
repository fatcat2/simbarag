#!/usr/bin/env python3
"""CLI tool to inspect the vector store contents."""

import argparse
import os

from dotenv import load_dotenv

from blueprints.rag.logic import (
    get_vector_store_stats,
    index_documents,
    list_all_documents,
)

# Load .env from the root directory
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
env_path = os.path.join(root_dir, ".env")
load_dotenv(env_path)


def print_stats():
    """Print vector store statistics."""
    stats = get_vector_store_stats()
    print("=== Vector Store Statistics ===")
    print(f"Collection Name: {stats['collection_name']}")
    print(f"Total Documents: {stats['total_documents']}")
    print()


def print_documents(limit: int = 10, show_content: bool = False):
    """Print documents in the vector store."""
    docs = list_all_documents(limit=limit)
    print(f"=== Documents (showing {len(docs)} of {limit} requested) ===\n")

    for i, doc in enumerate(docs, 1):
        print(f"Document {i}:")
        print(f"  ID: {doc['id']}")
        print(f"  Metadata: {doc['metadata']}")
        if show_content:
            print(f"  Content Preview: {doc['content_preview']}")
        print()


async def run_index():
    """Run the indexing process."""
    print("Starting indexing process...")
    await index_documents()
    print("Indexing complete!")
    print_stats()


def main():
    import asyncio

    parser = argparse.ArgumentParser(description="Inspect the vector store contents")
    parser.add_argument(
        "--stats", action="store_true", help="Show vector store statistics"
    )
    parser.add_argument(
        "--list", type=int, metavar="N", help="List N documents from the vector store"
    )
    parser.add_argument(
        "--show-content",
        action="store_true",
        help="Show content preview when listing documents",
    )
    parser.add_argument(
        "--index",
        action="store_true",
        help="Index documents from Paperless-NGX into the vector store",
    )

    args = parser.parse_args()

    # Handle indexing first if requested
    if args.index:
        asyncio.run(run_index())
        return

    # If no arguments provided, show stats by default
    if not any([args.stats, args.list]):
        args.stats = True

    if args.stats:
        print_stats()

    if args.list:
        print_documents(limit=args.list, show_content=args.show_content)


if __name__ == "__main__":
    main()
