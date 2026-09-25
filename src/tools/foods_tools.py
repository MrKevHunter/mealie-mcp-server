import logging
import traceback
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from mealie import MealieFetcher

logger = logging.getLogger("mealie-mcp")


def register_foods_tools(mcp: FastMCP, mealie: MealieFetcher) -> None:
    """Register all food-related tools with the MCP server."""

    @mcp.tool()
    def get_foods(
        search: Optional[str] = None,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
    ) -> Dict[str, Any]:
        """List the household's foods, optionally filtered by a search term.

        Use this to resolve an existing Mealie food id+name before building a
        structured ingredient, instead of hardcoding UUIDs. The Mealie search is
        token-based; do client-side matching against the returned items if you
        need fuzzy matching (e.g. "Basmatireis" -> "Reis").

        Args:
            search: Search term to filter foods by name/alias.
            page: Page number to retrieve.
            per_page: Number of items per page.

        Returns:
            Dict[str, Any]: Foods (under "items") with pagination information.
        """
        try:
            logger.info(
                {"message": "Fetching foods", "search": search, "per_page": per_page}
            )
            return mealie.get_foods(search=search, page=page, per_page=per_page)
        except Exception as e:
            error_msg = f"Error fetching foods: {str(e)}"
            logger.error({"message": error_msg})
            logger.debug(
                {"message": "Error traceback", "traceback": traceback.format_exc()}
            )
            raise ToolError(error_msg)

    @mcp.tool()
    def create_food(
        name: str,
        plural_name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new food.

        Args:
            name: Name of the food (e.g. "Reis").
            plural_name: Optional plural name.
            description: Optional description.

        Returns:
            Dict[str, Any]: The created food.
        """
        try:
            logger.info({"message": "Creating food", "name": name})
            return mealie.create_food(
                name, plural_name=plural_name, description=description
            )
        except Exception as e:
            error_msg = f"Error creating food '{name}': {str(e)}"
            logger.error({"message": error_msg})
            logger.debug(
                {"message": "Error traceback", "traceback": traceback.format_exc()}
            )
            raise ToolError(error_msg)

    @mcp.tool()
    def get_food(food_id: str) -> Dict[str, Any]:
        """Get a specific food by ID.

        Args:
            food_id: The UUID of the food.

        Returns:
            Dict[str, Any]: The food details.
        """
        try:
            logger.info({"message": "Fetching food", "food_id": food_id})
            return mealie.get_food(food_id)
        except Exception as e:
            error_msg = f"Error fetching food '{food_id}': {str(e)}"
            logger.error({"message": error_msg})
            logger.debug(
                {"message": "Error traceback", "traceback": traceback.format_exc()}
            )
            raise ToolError(error_msg)

    @mcp.tool()
    def update_food(
        food_id: str,
        name: Optional[str] = None,
        plural_name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update a food's details (only provided fields are changed).

        Args:
            food_id: The UUID of the food to update.
            name: New name for the food.
            plural_name: New plural name.
            description: New description.

        Returns:
            Dict[str, Any]: The updated food.
        """
        try:
            logger.info({"message": "Updating food", "food_id": food_id})

            food_data: Dict[str, Any] = {}
            if name is not None:
                food_data["name"] = name
            if plural_name is not None:
                food_data["pluralName"] = plural_name
            if description is not None:
                food_data["description"] = description

            if not food_data:
                raise ValueError("At least one field must be provided to update")

            return mealie.update_food(food_id, food_data)
        except Exception as e:
            error_msg = f"Error updating food '{food_id}': {str(e)}"
            logger.error({"message": error_msg})
            logger.debug(
                {"message": "Error traceback", "traceback": traceback.format_exc()}
            )
            raise ToolError(error_msg)

    @mcp.tool()
    def delete_food(food_id: str) -> Dict[str, Any]:
        """Delete a specific food.

        Args:
            food_id: The UUID of the food to delete.

        Returns:
            Dict[str, Any]: Confirmation of deletion.
        """
        try:
            logger.info({"message": "Deleting food", "food_id": food_id})
            return mealie.delete_food(food_id)
        except Exception as e:
            error_msg = f"Error deleting food '{food_id}': {str(e)}"
            logger.error({"message": error_msg})
            logger.debug(
                {"message": "Error traceback", "traceback": traceback.format_exc()}
            )
            raise ToolError(error_msg)

    @mcp.tool()
    def set_food_on_hand(food_id: str, on_hand: bool = True) -> Dict[str, Any]:
        """Mark or unmark a food as on-hand for the current household.

        Args:
            food_id: The UUID of the food.
            on_hand: True to mark on-hand, False to clear it. Defaults to True.

        Returns:
            Dict[str, Any]: The updated food.
        """
        try:
            logger.info(
                {
                    "message": "Setting food on-hand status",
                    "food_id": food_id,
                    "on_hand": on_hand,
                }
            )
            return mealie.set_food_on_hand(food_id, on_hand=on_hand)
        except Exception as e:
            error_msg = f"Error setting on-hand status for food '{food_id}': {str(e)}"
            logger.error({"message": error_msg})
            logger.debug(
                {"message": "Error traceback", "traceback": traceback.format_exc()}
            )
            raise ToolError(error_msg)

    @mcp.tool()
    def mark_foods_on_hand(names: List[str], on_hand: bool = True) -> Dict[str, Any]:
        """Mark or unmark common ingredients as on-hand, by name.

        Use this instead of set_food_on_hand when you know ingredient names
        (e.g. pantry staples like "Salt", "Flour", "Olive Oil") but not their
        Mealie food IDs. Names are matched case-insensitively against
        existing foods; a name with no match is created as a new food.

        Args:
            names: Food names to update.
            on_hand: True to mark on-hand, False to clear it. Defaults to True.

        Returns:
            Dict[str, Any]: {"updated": [...updated foods], "created": [...names of foods that were created]}.
        """
        try:
            logger.info(
                {"message": "Marking foods on-hand", "names": names, "on_hand": on_hand}
            )
            return mealie.set_foods_on_hand_by_name(names, on_hand=on_hand)
        except Exception as e:
            error_msg = f"Error marking foods on-hand: {str(e)}"
            logger.error({"message": error_msg})
            logger.debug(
                {"message": "Error traceback", "traceback": traceback.format_exc()}
            )
            raise ToolError(error_msg)

    @mcp.tool()
    def set_food_aliases(food_id: str, aliases: List[str]) -> Dict[str, Any]:
        """Replace a food's aliases with the given list.

        Aliases let Mealie match alternate names for a food (e.g. "Scallion"
        as an alias for "Green Onion") when parsing ingredients. This
        replaces the whole list; pass an empty list to clear all aliases, or
        use add_food_alias/remove_food_alias to change one at a time.

        Args:
            food_id: The UUID of the food.
            aliases: Alias names to set, e.g. ["Scallion", "Spring Onion"].

        Returns:
            Dict[str, Any]: The updated food.
        """
        try:
            logger.info(
                {
                    "message": "Setting food aliases",
                    "food_id": food_id,
                    "aliases": aliases,
                }
            )
            return mealie.set_food_aliases(food_id, aliases)
        except Exception as e:
            error_msg = f"Error setting aliases for food '{food_id}': {str(e)}"
            logger.error({"message": error_msg})
            logger.debug(
                {"message": "Error traceback", "traceback": traceback.format_exc()}
            )
            raise ToolError(error_msg)

    @mcp.tool()
    def add_food_alias(food_id: str, alias: str) -> Dict[str, Any]:
        """Add an alias to a food, keeping any aliases it already has.

        Args:
            food_id: The UUID of the food.
            alias: Alias name to add, e.g. "Scallion".

        Returns:
            Dict[str, Any]: The updated food.
        """
        try:
            logger.info(
                {"message": "Adding food alias", "food_id": food_id, "alias": alias}
            )
            return mealie.add_food_alias(food_id, alias)
        except Exception as e:
            error_msg = f"Error adding alias to food '{food_id}': {str(e)}"
            logger.error({"message": error_msg})
            logger.debug(
                {"message": "Error traceback", "traceback": traceback.format_exc()}
            )
            raise ToolError(error_msg)

    @mcp.tool()
    def set_food_label(food_id: str, label_id: Optional[str] = None) -> Dict[str, Any]:
        """Set or clear a food's label.

        Args:
            food_id: The UUID of the food.
            label_id: The UUID of the label to assign. Omit or pass None to
                clear the food's label.

        Returns:
            Dict[str, Any]: The updated food.
        """
        try:
            logger.info(
                {
                    "message": "Setting food label",
                    "food_id": food_id,
                    "label_id": label_id,
                }
            )
            return mealie.set_food_label(food_id, label_id)
        except Exception as e:
            error_msg = f"Error setting label for food '{food_id}': {str(e)}"
            logger.error({"message": error_msg})
            logger.debug(
                {"message": "Error traceback", "traceback": traceback.format_exc()}
            )
            raise ToolError(error_msg)

    @mcp.tool()
    def set_food_label_by_name(food_name: str, label_name: str) -> Dict[str, Any]:
        """Set a food's label, resolving both the food and label by name.

        Use this instead of set_food_label when you know the food and label
        names but not their Mealie IDs. Both are matched case-insensitively;
        the food must already exist, but the label is created if no label
        with that name exists yet.

        Args:
            food_name: Name of the food to update, e.g. "Carrot".
            label_name: Name of the label to assign, e.g. "Produce".

        Returns:
            Dict[str, Any]: The updated food.
        """
        try:
            logger.info(
                {
                    "message": "Setting food label by name",
                    "food_name": food_name,
                    "label_name": label_name,
                }
            )
            return mealie.set_food_label_by_name(food_name, label_name)
        except Exception as e:
            error_msg = (
                f"Error setting label '{label_name}' for food '{food_name}': {str(e)}"
            )
            logger.error({"message": error_msg})
            logger.debug(
                {"message": "Error traceback", "traceback": traceback.format_exc()}
            )
            raise ToolError(error_msg)

    @mcp.tool()
    def set_foods_label_by_name(
        food_names: List[str], label_name: str
    ) -> Dict[str, Any]:
        """Set one label on multiple foods at once, by name.

        Use this instead of calling set_food_label_by_name repeatedly when
        applying the same label to a batch of foods (e.g. tagging a set of
        ingredients as "Produce"). The label is resolved once (created if it
        doesn't exist) and applied to every matching food; food names are
        matched case-insensitively and are NOT auto-created, so a typo is
        reported instead of silently creating a new food.

        Args:
            food_names: Names of the foods to update, e.g. ["Carrot", "Onion"].
            label_name: Name of the label to assign to all of them, e.g. "Produce".

        Returns:
            Dict[str, Any]: {"updated": [...updated foods], "not_found": [...names with no matching food]}.
        """
        try:
            logger.info(
                {
                    "message": "Setting label on foods by name",
                    "food_names": food_names,
                    "label_name": label_name,
                }
            )
            return mealie.set_foods_label_by_name(food_names, label_name)
        except Exception as e:
            error_msg = f"Error setting label '{label_name}' on foods: {str(e)}"
            logger.error({"message": error_msg})
            logger.debug(
                {"message": "Error traceback", "traceback": traceback.format_exc()}
            )
            raise ToolError(error_msg)

    @mcp.tool()
    def remove_food_alias(food_id: str, alias: str) -> Dict[str, Any]:
        """Remove an alias from a food.

        Args:
            food_id: The UUID of the food.
            alias: Alias name to remove (matched case-insensitively).

        Returns:
            Dict[str, Any]: The updated food.
        """
        try:
            logger.info(
                {"message": "Removing food alias", "food_id": food_id, "alias": alias}
            )
            return mealie.remove_food_alias(food_id, alias)
        except Exception as e:
            error_msg = f"Error removing alias from food '{food_id}': {str(e)}"
            logger.error({"message": error_msg})
            logger.debug(
                {"message": "Error traceback", "traceback": traceback.format_exc()}
            )
            raise ToolError(error_msg)
