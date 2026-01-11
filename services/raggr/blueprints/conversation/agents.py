from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI

from blueprints.rag.logic import query_vector_store

openai_gpt_5_mini = ChatOpenAI(model="gpt-5-mini")


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


main_agent = create_agent(model=openai_gpt_5_mini, tools=[simba_search])
