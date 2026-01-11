#!/usr/bin/env python3
"""Management script for vector store operations."""

import argparse
import asyncio
import sys

from blueprints.rag.logic import (
    get_vector_store_stats,
    index_documents,
    list_all_documents,
    vector_store,
)


def stats():
    """Show vector store statistics."""
    stats = get_vector_store_stats()
    print("=== Vector Store Statistics ===")
    print(f"Collection: {stats['collection_name']}")
    print(f"Total Documents: {stats['total_documents']}")


async def index():
    """Index documents from Paperless-NGX."""
    print("Starting indexing process...")
    print("Fetching documents from Paperless-NGX...")
    await index_documents()
    print("✓ Indexing complete!")
    stats()


async def reindex():
    """Clear and reindex all documents."""
    print("Clearing existing documents...")
    collection = vector_store._collection
    all_docs = collection.get()

    if all_docs["ids"]:
        print(f"Deleting {len(all_docs['ids'])} existing documents...")
        collection.delete(ids=all_docs["ids"])
        print("✓ Cleared")
    else:
        print("Collection is already empty")

    await index()


def list_docs(limit: int = 10, show_content: bool = False):
    """List documents in the vector store."""
    docs = list_all_documents(limit=limit)
    print(f"\n=== Documents (showing {len(docs)}) ===\n")

    for i, doc in enumerate(docs, 1):
        print(f"Document {i}:")
        print(f"  ID: {doc['id']}")
        print(f"  Metadata: {doc['metadata']}")
        if show_content:
            print(f"  Content: {doc['content_preview']}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Manage vector store for RAG system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s stats                    # Show vector store statistics
  %(prog)s index                    # Index new documents from Paperless-NGX
  %(prog)s reindex                  # Clear and reindex all documents
  %(prog)s list 10                  # List first 10 documents
  %(prog)s list 20 --show-content   # List 20 documents with content preview
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Stats command
    subparsers.add_parser("stats", help="Show vector store statistics")

    # Index command
    subparsers.add_parser("index", help="Index documents from Paperless-NGX")

    # Reindex command
    subparsers.add_parser("reindex", help="Clear and reindex all documents")

    # List command
    list_parser = subparsers.add_parser("list", help="List documents in vector store")
    list_parser.add_argument(
        "limit", type=int, default=10, nargs="?", help="Number of documents to list"
    )
    list_parser.add_argument(
        "--show-content", action="store_true", help="Show content preview"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "stats":
            stats()
        elif args.command == "index":
            asyncio.run(index())
        elif args.command == "reindex":
            asyncio.run(reindex())
        elif args.command == "list":
            list_docs(limit=args.limit, show_content=args.show_content)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
