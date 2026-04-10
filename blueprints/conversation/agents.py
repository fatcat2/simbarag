import os
from typing import cast

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import BaseChatModel
from langchain.tools import tool
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from tavily import AsyncTavilyClient

from blueprints.conversation.memory import save_memory
from blueprints.rag.logic import query_vector_store
from utils.obsidian_service import ObsidianService
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

# Initialize Obsidian service (will only work if OBSIDIAN_VAULT_PATH is set)
try:
    obsidian_service = ObsidianService()
    obsidian_enabled = True
except (ValueError, Exception) as e:
    print(f"Obsidian service not initialized: {e}")
    obsidian_enabled = False


@tool
def get_current_date() -> str:
    """Get today's date in a human-readable format.

    Use this tool when you need to:
    - Reference today's date in your response
    - Answer questions like "what is today's date"
    - Format dates in messages or documents
    - Calculate time periods relative to today

    Returns:
        Today's date in YYYY-MM-DD format
    """
    from datetime import date

    return date.today().isoformat()


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


@tool
async def obsidian_search_notes(query: str) -> str:
    """Search through Obsidian vault notes for information.

    Use this tool when you need to:
    - Find information in personal notes
    - Research past ideas or thoughts from your vault
    - Look up information stored in markdown files
    - Search for content that would be in your notes

    Args:
        query: The search query to look up in your Obsidian vault

    Returns:
        Relevant notes with their content and metadata
    """
    if not obsidian_enabled:
        return "Obsidian integration is not configured. Please set OBSIDIAN_VAULT_PATH environment variable."

    try:
        # Query ChromaDB for obsidian documents
        serialized, docs = await query_vector_store(query=query)
        return serialized

    except Exception as e:
        return f"Error searching Obsidian notes: {str(e)}"


@tool
async def obsidian_read_note(relative_path: str) -> str:
    """Read a specific note from your Obsidian vault.

    Use this tool when you want to:
    - Read the full content of a specific note
    - Get detailed information from a particular markdown file
    - Access content from a known note path

    Args:
        relative_path: Path to note relative to vault root (e.g., "notes/my-note.md")

    Returns:
        Full content and metadata of the requested note
    """
    if not obsidian_enabled:
        return "Obsidian integration is not configured. Please set OBSIDIAN_VAULT_PATH environment variable."

    try:
        note = obsidian_service.read_note(relative_path)
        content_data = note["content"]

        result = f"File: {note['path']}\n\n"
        result += f"Frontmatter:\n{content_data['metadata']}\n\n"
        result += f"Content:\n{content_data['content']}\n\n"
        result += f"Tags: {', '.join(content_data['tags'])}\n"
        result += f"Contains {len(content_data['wikilinks'])} wikilinks and {len(content_data['embeds'])} embeds"

        return result

    except FileNotFoundError:
        return f"Note not found at '{relative_path}'. Please check the path is correct."
    except Exception as e:
        return f"Error reading note: {str(e)}"


@tool
async def obsidian_create_note(
    title: str,
    content: str,
    folder: str = "notes",
    tags: str = "",
) -> str:
    """Create a new note in your Obsidian vault.

    Use this tool when you want to:
    - Save research findings or ideas to your vault
    - Create a new document with a specific title
    - Write notes for future reference

    Args:
        title: The title of the note (will be used as filename)
        content: The body content of the note
        folder: The folder where to create the note (default: "notes")
        tags: Comma-separated list of tags to add (default: "")

    Returns:
        Path to the created note
    """
    if not obsidian_enabled:
        return "Obsidian integration is not configured. Please set OBSIDIAN_VAULT_PATH environment variable."

    try:
        # Parse tags from comma-separated string
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

        relative_path = obsidian_service.create_note(
            title=title,
            content=content,
            folder=folder,
            tags=tag_list,
        )

        return f"Successfully created note: {relative_path}"

    except Exception as e:
        return f"Error creating note: {str(e)}"


@tool
def journal_get_today() -> str:
    """Get today's daily journal note, including all tasks and log entries.

    Use this tool when the user asks about:
    - What's on their plate today
    - Today's tasks or to-do list
    - Today's journal entry
    - What they've logged today

    Returns:
        The full content of today's daily note, or a message if it doesn't exist.
    """
    if not obsidian_enabled:
        return "Obsidian integration is not configured."

    try:
        note = obsidian_service.get_daily_note()
        if not note["found"]:
            return f"No daily note found for {note['date']}. Use journal_add_task to create one."
        return f"Daily note for {note['date']}:\n\n{note['content']}"
    except Exception as e:
        return f"Error reading daily note: {str(e)}"


@tool
def journal_get_tasks(date: str = "") -> str:
    """Get tasks from a daily journal note.

    Use this tool when the user asks about:
    - Open or pending tasks for a day
    - What tasks are done or not done
    - Task status for today or a specific date

    Args:
        date: Date in YYYY-MM-DD format (optional, defaults to today)

    Returns:
        List of tasks with their completion status.
    """
    if not obsidian_enabled:
        return "Obsidian integration is not configured."

    try:
        from datetime import datetime as dt

        parsed_date = dt.strptime(date, "%Y-%m-%d") if date else None
        result = obsidian_service.get_daily_tasks(parsed_date)

        if not result["found"]:
            return f"No daily note found for {result['date']}."

        if not result["tasks"]:
            return f"No tasks found in the {result['date']} note."

        lines = [f"Tasks for {result['date']}:"]
        for task in result["tasks"]:
            status = "[x]" if task["done"] else "[ ]"
            lines.append(f"- {status} {task['text']}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error reading tasks: {str(e)}"


@tool
def journal_add_task(task: str, date: str = "") -> str:
    """Add a task to a daily journal note.

    Use this tool when the user wants to:
    - Add a task or to-do to today's note
    - Remind themselves to do something
    - Track a new item in their daily note

    Args:
        task: The task description to add
        date: Date in YYYY-MM-DD format (optional, defaults to today)

    Returns:
        Confirmation of the added task.
    """
    if not obsidian_enabled:
        return "Obsidian integration is not configured."

    try:
        from datetime import datetime as dt

        parsed_date = dt.strptime(date, "%Y-%m-%d") if date else None
        result = obsidian_service.add_task_to_daily_note(task, parsed_date)

        if result["success"]:
            note_date = date or dt.now().strftime("%Y-%m-%d")
            extra = " (created new note)" if result["created_note"] else ""
            return f"Added task '{task}' to {note_date}{extra}."
        return "Failed to add task."
    except Exception as e:
        return f"Error adding task: {str(e)}"


@tool
def journal_complete_task(task: str, date: str = "") -> str:
    """Mark a task as complete in a daily journal note.

    Use this tool when the user wants to:
    - Check off a task as done
    - Mark something as completed
    - Update task status in their daily note

    Args:
        task: The task text to mark complete (exact or partial match)
        date: Date in YYYY-MM-DD format (optional, defaults to today)

    Returns:
        Confirmation that the task was marked complete.
    """
    if not obsidian_enabled:
        return "Obsidian integration is not configured."

    try:
        from datetime import datetime as dt

        parsed_date = dt.strptime(date, "%Y-%m-%d") if date else None
        result = obsidian_service.complete_task_in_daily_note(task, parsed_date)

        if result["success"]:
            return f"Marked '{result['completed_task']}' as complete."
        return f"Could not complete task: {result.get('error', 'unknown error')}"
    except Exception as e:
        return f"Error completing task: {str(e)}"


@tool
async def obsidian_create_task(
    title: str,
    content: str = "",
    folder: str = "tasks",
    due_date: str = "",
    tags: str = "",
) -> str:
    """Create a new task note in your Obsidian vault.

    Use this tool when you want to:
    - Create a task to remember to do something
    - Add a task with a due date
    - Track tasks in your vault

    Args:
        title: The title of the task
        content: The description of the task (optional)
        folder: The folder to place the task (default: "tasks")
        due_date: Due date in YYYY-MM-DD format (optional)
        tags: Comma-separated list of tags to add (optional)

    Returns:
        Path to the created task note
    """
    if not obsidian_enabled:
        return "Obsidian integration is not configured. Please set OBSIDIAN_VAULT_PATH environment variable."

    try:
        # Parse tags from comma-separated string
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

        relative_path = obsidian_service.create_task(
            title=title,
            content=content,
            folder=folder,
            due_date=due_date or None,
            tags=tag_list,
        )

        return f"Successfully created task: {relative_path}"

    except Exception as e:
        return f"Error creating task: {str(e)}"


@tool
async def save_user_memory(content: str, config: RunnableConfig) -> str:
    """Save a fact or preference about the user for future conversations.

    Use this tool when the user:
    - Explicitly asks you to remember something ("remember that...", "keep in mind...")
    - Shares a personal preference that would be useful in future conversations
      (e.g., "I prefer metric units", "my cat's name is Luna")
    - Tells you a meaningful personal fact (e.g., "I'm allergic to peanuts")

    Do NOT save:
    - Trivial or ephemeral info (e.g., "I'm tired today")
    - Information already in the system prompt or documents
    - Conversation-specific context that won't matter later

    Args:
        content: A concise statement of the fact or preference to remember.
                 Write it as a standalone sentence (e.g., "User prefers dark mode"
                 rather than "likes dark mode").

    Returns:
        Confirmation that the memory was saved.
    """
    user_id = config["configurable"]["user_id"]
    return await save_memory(user_id=user_id, content=content)


# Create tools list based on what's available
tools = [get_current_date, simba_search, web_search, save_user_memory]
if ynab_enabled:
    tools.extend(
        [
            ynab_budget_summary,
            ynab_search_transactions,
            ynab_category_spending,
            ynab_insights,
        ]
    )
if obsidian_enabled:
    tools.extend(
        [
            obsidian_search_notes,
            obsidian_read_note,
            obsidian_create_note,
            obsidian_create_task,
            journal_get_today,
            journal_get_tasks,
            journal_add_task,
            journal_complete_task,
        ]
    )

# Llama 3.1 supports native function calling via OpenAI-compatible API
main_agent = create_agent(model=model_with_fallback, tools=tools)
