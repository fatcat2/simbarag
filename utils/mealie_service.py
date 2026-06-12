"""Mealie API service for querying meal plans, recipes, and shopping lists."""

import os
import logging
from datetime import datetime, timedelta
from typing import Any, Optional
import httpx

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class MealieService:
    """Service for interacting with Mealie API."""

    def __init__(self):
        """Initialize Mealie API client."""
        logger.info("[MEALIE] Initializing Mealie service...")
        self.base_url = os.getenv("MEALIE_BASE_URL", "")
        self.api_token = os.getenv("MEALIE_API_TOKEN", "")

        if not self.base_url:
            logger.error("[MEALIE] MEALIE_BASE_URL not found in environment")
            raise ValueError("MEALIE_BASE_URL environment variable is required")

        if not self.api_token:
            logger.error("[MEALIE] MEALIE_API_TOKEN not found in environment")
            raise ValueError("MEALIE_API_TOKEN environment variable is required")

        # Remove trailing slash from base URL if present
        self.base_url = self.base_url.rstrip("/")

        logger.info(f"[MEALIE] Base URL: {self.base_url}")
        logger.info(f"[MEALIE] API token found: {self.api_token[:10]}...")

        # Create HTTP client
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

        logger.info("[MEALIE] Mealie service initialized successfully")

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def get_shopping_lists(self) -> dict[str, Any]:
        """Get all shopping lists with their items.

        Returns:
            Dictionary containing shopping lists and their items.
        """
        logger.info("[MEALIE] get_shopping_lists() called")

        try:
            logger.info("[MEALIE] Fetching shopping lists from Mealie API...")
            response = await self.client.get(
                f"{self.base_url}/api/households/shopping/lists"
            )
            response.raise_for_status()
            data = response.json()

            logger.info(
                f"[MEALIE] Retrieved {len(data.get('items', []))} shopping lists"
            )

            shopping_lists = []
            total_unchecked_items = 0

            for shopping_list in data.get("items", []):
                list_id = shopping_list.get("id")
                list_name = shopping_list.get("name", "Unnamed List")

                # Get items for this list
                items_response = await self.client.get(
                    f"{self.base_url}/api/households/shopping/items",
                    params={"shopping_list_id": list_id},
                )
                items_response.raise_for_status()
                items_data = items_response.json()

                unchecked_items = []
                checked_items = []

                for item in items_data.get("items", []):
                    item_data = {
                        "name": item.get("display", item.get("note", "Unknown item")),
                        "quantity": item.get("quantity", 1),
                        "note": item.get("note", ""),
                        "food": item.get("foodId"),
                    }

                    if item.get("checked", False):
                        checked_items.append(item_data)
                    else:
                        unchecked_items.append(item_data)
                        total_unchecked_items += 1

                shopping_lists.append(
                    {
                        "id": list_id,
                        "name": list_name,
                        "unchecked_items": unchecked_items,
                        "checked_items": checked_items,
                        "total_items": len(unchecked_items) + len(checked_items),
                    }
                )

            logger.info(
                f"[MEALIE] Processed {len(shopping_lists)} lists with {total_unchecked_items} unchecked items"
            )

            return {
                "shopping_lists": shopping_lists,
                "total_lists": len(shopping_lists),
                "total_unchecked_items": total_unchecked_items,
            }

        except httpx.HTTPStatusError as e:
            logger.error(
                f"[MEALIE] HTTP error in get_shopping_lists(): {e.response.status_code} - {e.response.text}"
            )
            raise
        except Exception as e:
            logger.error(
                f"[MEALIE] Error in get_shopping_lists(): {type(e).__name__}: {str(e)}"
            )
            logger.exception("[MEALIE] Full traceback:")
            raise

    async def get_meal_plans(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict[str, Any]:
        """Get meal plans for a date range.

        Args:
            start_date: Start date in YYYY-MM-DD format (defaults to today)
            end_date: End date in YYYY-MM-DD format (defaults to 7 days from start)

        Returns:
            Dictionary containing meal plans for the specified date range.
        """
        logger.info(
            f"[MEALIE] get_meal_plans() called - start_date={start_date}, end_date={end_date}"
        )

        try:
            # Set default dates
            if not start_date:
                start_date = datetime.now().strftime("%Y-%m-%d")
            if not end_date:
                # Default to 7 days from start
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = start_dt + timedelta(days=7)
                end_date = end_dt.strftime("%Y-%m-%d")

            logger.info(f"[MEALIE] Fetching meal plans from {start_date} to {end_date}")

            response = await self.client.get(
                f"{self.base_url}/api/households/mealplans",
                params={"start_date": start_date, "end_date": end_date},
            )
            response.raise_for_status()
            data = response.json()

            logger.info(f"[MEALIE] Retrieved {len(data.get('items', []))} meal plans")

            meal_plans = []
            for plan in data.get("items", []):
                meal_plans.append(
                    {
                        "id": plan.get("id"),
                        "date": plan.get("date"),
                        "entry_type": plan.get("entryType", "unknown"),
                        "title": plan.get("title", ""),
                        "recipe_name": plan.get("recipeName", ""),
                        "recipe_slug": plan.get("recipeSlug", ""),
                        "note": plan.get("note", ""),
                    }
                )

            # Group by date
            plans_by_date = {}
            for plan in meal_plans:
                date = plan["date"]
                if date not in plans_by_date:
                    plans_by_date[date] = []
                plans_by_date[date].append(plan)

            logger.info(f"[MEALIE] Organized into {len(plans_by_date)} unique dates")

            return {
                "meal_plans": meal_plans,
                "plans_by_date": plans_by_date,
                "start_date": start_date,
                "end_date": end_date,
                "total_plans": len(meal_plans),
            }

        except httpx.HTTPStatusError as e:
            logger.error(
                f"[MEALIE] HTTP error in get_meal_plans(): {e.response.status_code} - {e.response.text}"
            )
            raise
        except Exception as e:
            logger.error(
                f"[MEALIE] Error in get_meal_plans(): {type(e).__name__}: {str(e)}"
            )
            logger.exception("[MEALIE] Full traceback:")
            raise

    async def get_todays_meals(self) -> dict[str, Any]:
        """Get today's meal plans.

        Returns:
            Dictionary containing today's meal plans.
        """
        logger.info("[MEALIE] get_todays_meals() called")

        try:
            logger.info("[MEALIE] Fetching today's meals from Mealie API...")
            response = await self.client.get(
                f"{self.base_url}/api/households/mealplans/today"
            )
            response.raise_for_status()
            data = response.json()

            logger.info(
                f"[MEALIE] Retrieved {len(data.get('items', []))} meals for today"
            )

            meals = []
            for plan in data.get("items", []):
                meals.append(
                    {
                        "id": plan.get("id"),
                        "entry_type": plan.get("entryType", "unknown"),
                        "title": plan.get("title", ""),
                        "recipe_name": plan.get("recipeName", ""),
                        "recipe_slug": plan.get("recipeSlug", ""),
                        "note": plan.get("note", ""),
                    }
                )

            return {
                "today": datetime.now().strftime("%Y-%m-%d"),
                "meals": meals,
                "total_meals": len(meals),
            }

        except httpx.HTTPStatusError as e:
            logger.error(
                f"[MEALIE] HTTP error in get_todays_meals(): {e.response.status_code} - {e.response.text}"
            )
            raise
        except Exception as e:
            logger.error(
                f"[MEALIE] Error in get_todays_meals(): {type(e).__name__}: {str(e)}"
            )
            logger.exception("[MEALIE] Full traceback:")
            raise

    async def get_recipe(self, recipe_slug: str) -> dict[str, Any]:
        """Get recipe details by slug.

        Args:
            recipe_slug: The recipe's slug identifier

        Returns:
            Dictionary containing recipe details including ingredients and instructions.
        """
        logger.info(f"[MEALIE] get_recipe() called - recipe_slug={recipe_slug}")

        try:
            logger.info(f"[MEALIE] Fetching recipe '{recipe_slug}' from Mealie API...")
            response = await self.client.get(
                f"{self.base_url}/api/households/self/recipes/{recipe_slug}"
            )
            response.raise_for_status()
            recipe = response.json()

            logger.info(f"[MEALIE] Retrieved recipe: {recipe.get('name', 'Unknown')}")

            # Extract key information
            ingredients = []
            for ingredient in recipe.get("recipeIngredient", []):
                if isinstance(ingredient, dict):
                    ingredients.append(
                        {
                            "display": ingredient.get("display", ""),
                            "quantity": ingredient.get("quantity"),
                            "unit": ingredient.get("unit", {}).get("name", ""),
                            "food": ingredient.get("food", {}).get("name", ""),
                            "note": ingredient.get("note", ""),
                        }
                    )
                else:
                    # Sometimes ingredients are just strings
                    ingredients.append({"display": str(ingredient)})

            instructions = []
            for instruction in recipe.get("recipeInstructions", []):
                if isinstance(instruction, dict):
                    instructions.append(
                        {
                            "title": instruction.get("title", ""),
                            "text": instruction.get("text", ""),
                        }
                    )
                else:
                    instructions.append({"text": str(instruction)})

            return {
                "name": recipe.get("name", "Unknown Recipe"),
                "slug": recipe_slug,
                "description": recipe.get("description", ""),
                "ingredients": ingredients,
                "instructions": instructions,
                "prep_time": recipe.get("prepTime", ""),
                "cook_time": recipe.get("performTime", ""),
                "total_time": recipe.get("totalTime", ""),
                "servings": recipe.get("recipeYield", ""),
                "tags": [tag.get("name", "") for tag in recipe.get("tags", [])],
            }

        except httpx.HTTPStatusError as e:
            logger.error(
                f"[MEALIE] HTTP error in get_recipe(): {e.response.status_code} - {e.response.text}"
            )
            raise
        except Exception as e:
            logger.error(
                f"[MEALIE] Error in get_recipe(): {type(e).__name__}: {str(e)}"
            )
            logger.exception("[MEALIE] Full traceback:")
            raise

    async def create_meal_plan(
        self,
        date: str,
        entry_type: str = "dinner",
        recipe_slug: Optional[str] = None,
        title: Optional[str] = None,
        note: Optional[str] = None,
    ) -> dict[str, Any]:
        """Create a new meal plan entry.

        Args:
            date: Date in YYYY-MM-DD format
            entry_type: Type of meal (breakfast, lunch, dinner, side)
            recipe_slug: Recipe slug to add to the meal plan (optional)
            title: Custom title for the meal (optional, used if no recipe)
            note: Additional notes for the meal (optional)

        Returns:
            Dictionary containing the created meal plan entry.
        """
        logger.info(
            f"[MEALIE] create_meal_plan() called - date={date}, entry_type={entry_type}, recipe={recipe_slug}"
        )

        try:
            # Build request body
            body = {
                "date": date,
                "entryType": entry_type,
            }

            if recipe_slug:
                body["recipeId"] = recipe_slug  # API might use recipeId or recipeSlug
            if title:
                body["title"] = title
            if note:
                body["text"] = note  # API might use 'text' or 'note'

            logger.info(f"[MEALIE] Creating meal plan with body: {body}")

            response = await self.client.post(
                f"{self.base_url}/api/households/mealplans", json=body
            )
            response.raise_for_status()
            data = response.json()

            logger.info(
                f"[MEALIE] Successfully created meal plan entry with ID: {data.get('id')}"
            )

            return {
                "id": data.get("id"),
                "date": data.get("date"),
                "entry_type": data.get("entryType"),
                "title": data.get("title"),
                "recipe_name": data.get("recipeName"),
                "note": data.get("text", data.get("note", "")),
                "success": True,
            }

        except httpx.HTTPStatusError as e:
            logger.error(
                f"[MEALIE] HTTP error in create_meal_plan(): {e.response.status_code} - {e.response.text}"
            )
            raise
        except Exception as e:
            logger.error(
                f"[MEALIE] Error in create_meal_plan(): {type(e).__name__}: {str(e)}"
            )
            logger.exception("[MEALIE] Full traceback:")
            raise

    async def update_meal_plan(
        self,
        item_id: int,
        date: Optional[str] = None,
        entry_type: Optional[str] = None,
        recipe_slug: Optional[str] = None,
        title: Optional[str] = None,
        note: Optional[str] = None,
    ) -> dict[str, Any]:
        """Update an existing meal plan entry.

        Args:
            item_id: ID of the meal plan entry to update
            date: Date in YYYY-MM-DD format (optional)
            entry_type: Type of meal (breakfast, lunch, dinner, side) (optional)
            recipe_slug: Recipe slug to update (optional)
            title: Custom title for the meal (optional)
            note: Additional notes for the meal (optional)

        Returns:
            Dictionary containing the updated meal plan entry.
        """
        logger.info(f"[MEALIE] update_meal_plan() called - item_id={item_id}")

        try:
            # Build request body with only provided fields
            body = {}

            if date:
                body["date"] = date
            if entry_type:
                body["entryType"] = entry_type
            if recipe_slug:
                body["recipeId"] = recipe_slug
            if title:
                body["title"] = title
            if note:
                body["text"] = note

            logger.info(f"[MEALIE] Updating meal plan {item_id} with body: {body}")

            response = await self.client.put(
                f"{self.base_url}/api/households/mealplans/{item_id}", json=body
            )
            response.raise_for_status()
            data = response.json()

            logger.info(f"[MEALIE] Successfully updated meal plan entry {item_id}")

            return {
                "id": data.get("id"),
                "date": data.get("date"),
                "entry_type": data.get("entryType"),
                "title": data.get("title"),
                "recipe_name": data.get("recipeName"),
                "note": data.get("text", data.get("note", "")),
                "success": True,
            }

        except httpx.HTTPStatusError as e:
            logger.error(
                f"[MEALIE] HTTP error in update_meal_plan(): {e.response.status_code} - {e.response.text}"
            )
            raise
        except Exception as e:
            logger.error(
                f"[MEALIE] Error in update_meal_plan(): {type(e).__name__}: {str(e)}"
            )
            logger.exception("[MEALIE] Full traceback:")
            raise

    async def delete_meal_plan(self, item_id: int) -> dict[str, Any]:
        """Delete a meal plan entry.

        Args:
            item_id: ID of the meal plan entry to delete

        Returns:
            Dictionary containing success status and deleted entry info.
        """
        logger.info(f"[MEALIE] delete_meal_plan() called - item_id={item_id}")

        try:
            response = await self.client.delete(
                f"{self.base_url}/api/households/mealplans/{item_id}"
            )
            response.raise_for_status()
            data = response.json()

            logger.info(f"[MEALIE] Successfully deleted meal plan entry {item_id}")

            return {
                "id": item_id,
                "deleted": True,
                "entry": data,
            }

        except httpx.HTTPStatusError as e:
            logger.error(
                f"[MEALIE] HTTP error in delete_meal_plan(): {e.response.status_code} - {e.response.text}"
            )
            raise
        except Exception as e:
            logger.error(
                f"[MEALIE] Error in delete_meal_plan(): {type(e).__name__}: {str(e)}"
            )
            logger.exception("[MEALIE] Full traceback:")
            raise
