import os
from typing import cast

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import BaseChatModel
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from tavily import AsyncTavilyClient

from blueprints.rag.logic import query_vector_store
from utils.ynab_service import YNABService

# Load environment variables
load_dotenv()

# Configure LLM with llama-server or OpenAI fallback
llama_url = os.getenv("LLAMA_SERVER_URL")
if llama_url:
    llama_chat = ChatOpenAI(
        base_url=llama_url,
        api_key="not-needed",
        model=os.getenv("LLAMA_MODEL_NAME", "llama-3.1-8b-instruct"),
    )
else:
    llama_chat = None

openai_fallback = ChatOpenAI(model="gpt-5-mini")
model_with_fallback = cast(
    BaseChatModel,
    llama_chat.with_fallbacks([openai_fallback]) if llama_chat else openai_fallback,
)
client = AsyncTavilyClient(api_key=os.getenv("TAVILY_API_KEY", ""))

# Initialize YNAB service (will only work if YNAB_ACCESS_TOKEN is set)
try:
    ynab_service = YNABService()
    ynab_enabled = True
except (ValueError, Exception) as e:
    print(f"YNAB service not initialized: {e}")
    ynab_enabled = False


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


@tool
def ynab_budget_summary() -> str:
    """Get overall budget summary and health status from YNAB.

    Use this tool when the user asks about:
    - Overall budget health or status
    - How much money is to be budgeted
    - Total budget amounts or spending
    - General budget overview questions

    Returns:
        Summary of budget health, to-be-budgeted amount, total budgeted,
        total activity, and available amounts.
    """
    if not ynab_enabled:
        return "YNAB integration is not configured. Please set YNAB_ACCESS_TOKEN environment variable."

    try:
        summary = ynab_service.get_budget_summary()
        return summary["summary"]
    except Exception as e:
        return f"Error fetching budget summary: {str(e)}"


@tool
def ynab_search_transactions(
    start_date: str = "",
    end_date: str = "",
    category_name: str = "",
    payee_name: str = "",
) -> str:
    """Search YNAB transactions by date range, category, or payee.

    Use this tool when the user asks about:
    - Specific transactions or purchases
    - Spending at a particular store or payee
    - Transactions in a specific category
    - What was spent during a time period

    Args:
        start_date: Start date in YYYY-MM-DD format (optional, defaults to 30 days ago)
        end_date: End date in YYYY-MM-DD format (optional, defaults to today)
        category_name: Filter by category name (optional, partial match)
        payee_name: Filter by payee/store name (optional, partial match)

    Returns:
        List of matching transactions with dates, amounts, categories, and payees.
    """
    if not ynab_enabled:
        return "YNAB integration is not configured. Please set YNAB_ACCESS_TOKEN environment variable."

    try:
        result = ynab_service.get_transactions(
            start_date=start_date or None,
            end_date=end_date or None,
            category_name=category_name or None,
            payee_name=payee_name or None,
        )

        if result["count"] == 0:
            return "No transactions found matching the specified criteria."

        # Format transactions for readability
        txn_list = []
        for txn in result["transactions"][:10]:  # Limit to 10 for readability
            txn_list.append(
                f"- {txn['date']}: {txn['payee']} - ${abs(txn['amount']):.2f} ({txn['category'] or 'Uncategorized'})"
            )

        return (
            f"Found {result['count']} transactions from {result['start_date']} to {result['end_date']}. "
            f"Total: ${abs(result['total_amount']):.2f}\n\n"
            + "\n".join(txn_list)
            + (
                f"\n\n(Showing first 10 of {result['count']} transactions)"
                if result["count"] > 10
                else ""
            )
        )
    except Exception as e:
        return f"Error searching transactions: {str(e)}"


@tool
def ynab_category_spending(month: str = "") -> str:
    """Get spending breakdown by category for a specific month.

    Use this tool when the user asks about:
    - Spending by category
    - What categories were overspent
    - Monthly spending breakdown
    - Budget vs actual spending for a month

    Args:
        month: Month in YYYY-MM format (optional, defaults to current month)

    Returns:
        Spending breakdown by category with budgeted, spent, and available amounts.
    """
    if not ynab_enabled:
        return "YNAB integration is not configured. Please set YNAB_ACCESS_TOKEN environment variable."

    try:
        result = ynab_service.get_category_spending(month=month or None)

        summary = (
            f"Budget spending for {result['month']}:\n"
            f"Total budgeted: ${result['total_budgeted']:.2f}\n"
            f"Total spent: ${result['total_spent']:.2f}\n"
            f"Total available: ${result['total_available']:.2f}\n"
        )

        if result["overspent_categories"]:
            summary += (
                f"\nOverspent categories ({len(result['overspent_categories'])}):\n"
            )
            for cat in result["overspent_categories"][:5]:
                summary += f"- {cat['name']}: Budgeted ${cat['budgeted']:.2f}, Spent ${cat['spent']:.2f}, Over by ${cat['overspent_by']:.2f}\n"

        # Add top spending categories
        summary += "\nTop spending categories:\n"
        for cat in result["categories"][:10]:
            if cat["activity"] < 0:  # Only show spending (negative activity)
                summary += f"- {cat['category']}: ${abs(cat['activity']):.2f} (budgeted: ${cat['budgeted']:.2f}, available: ${cat['available']:.2f})\n"

        return summary
    except Exception as e:
        return f"Error fetching category spending: {str(e)}"


@tool
def ynab_insights(months_back: int = 3) -> str:
    """Generate insights about spending patterns and budget health over time.

    Use this tool when the user asks about:
    - Spending trends or patterns
    - Budget recommendations
    - Which categories are frequently overspent
    - How current spending compares to past months
    - Overall budget health analysis

    Args:
        months_back: Number of months to analyze (default 3, max 6)

    Returns:
        Insights about spending trends, frequently overspent categories,
        and personalized recommendations.
    """
    if not ynab_enabled:
        return "YNAB integration is not configured. Please set YNAB_ACCESS_TOKEN environment variable."

    try:
        # Limit to reasonable range
        months_back = min(max(1, months_back), 6)
        result = ynab_service.get_spending_insights(months_back=months_back)

        if "error" in result:
            return result["error"]

        summary = (
            f"Spending insights for the last {months_back} months:\n\n"
            f"Average monthly spending: ${result['average_monthly_spending']:.2f}\n"
            f"Current month spending: ${result['current_month_spending']:.2f}\n"
            f"Spending trend: {result['spending_trend']}\n"
        )

        if result["frequently_overspent_categories"]:
            summary += "\nFrequently overspent categories:\n"
            for cat in result["frequently_overspent_categories"][:5]:
                summary += f"- {cat['category']}: overspent in {cat['months_overspent']} of {months_back} months\n"

        if result["recommendations"]:
            summary += "\nRecommendations:\n"
            for rec in result["recommendations"]:
                summary += f"- {rec}\n"

        return summary
    except Exception as e:
        return f"Error generating insights: {str(e)}"


# Create tools list based on what's available
tools = [simba_search, web_search]
if ynab_enabled:
    tools.extend(
        [
            ynab_budget_summary,
            ynab_search_transactions,
            ynab_category_spending,
            ynab_insights,
        ]
    )

# Llama 3.1 supports native function calling via OpenAI-compatible API
main_agent = create_agent(model=model_with_fallback, tools=tools)
