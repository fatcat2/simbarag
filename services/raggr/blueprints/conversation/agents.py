import os
from typing import cast

from langchain.agents import create_agent
from langchain.chat_models import BaseChatModel
from langchain.tools import tool
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from tavily import AsyncTavilyClient

from blueprints.rag.logic import query_vector_store

openai_gpt_5_mini = ChatOpenAI(model="gpt-5-mini")
ollama_deepseek = ChatOllama(model="llama3.1:8b", base_url=os.getenv("OLLAMA_URL"))
model_with_fallback = cast(
    BaseChatModel, ollama_deepseek.with_fallbacks([openai_gpt_5_mini])
)
client = AsyncTavilyClient(os.getenv("TAVILY_KEY"), "")


@tool
async def web_search(query: str) -> str:
    """Search the web for current information using Tavily.

    Use this tool when you need to:
    - Find current information not in the knowledge base
    - Look up recent events, news, or updates
    - Verify facts or get additional context
    - Search for information outside of Simba's documents

    Args:
        query: The search query to look up on the web

    Returns:
        Search results from the web with titles, content, and source URLs
    """
    response = await client.search(query=query, search_depth="basic")
    results = response.get("results", [])

    if not results:
        return "No results found for the query."

    formatted = "\n\n".join(
        [
            f"**{result['title']}**\n{result['content']}\nSource: {result['url']}"
            for result in results[:5]
        ]
    )
    return formatted


@tool(response_format="content_and_artifact")
async def simba_search(query: str):
    """Search through Simba's medical records, veterinary documents, and personal information.

    Use this tool whenever the user asks questions about:
    - Simba's health history, medical records, or veterinary visits
    - Medications, treatments, or diagnoses
    - Weight, diet, or physical characteristics over time
    - Veterinary recommendations or advice
    - Ryan's (the owner's) information related to Simba
    - Any factual information that would be found in documents

    Args:
        query: The user's question or information need about Simba

    Returns:
        Relevant information from Simba's documents
    """
    print(f"[SIMBA SEARCH] Tool called with query: {query}")
    serialized, docs = await query_vector_store(query=query)
    print(f"[SIMBA SEARCH] Found {len(docs)} documents")
    print(f"[SIMBA SEARCH] Serialized result length: {len(serialized)}")
    print(f"[SIMBA SEARCH] First 200 chars: {serialized[:200]}")
    return serialized, docs


main_agent = create_agent(model=model_with_fallback, tools=[simba_search, web_search])
