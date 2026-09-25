import logging
import traceback
from typing import Any, Dict, Optional

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from mealie import MealieFetcher

logger = logging.getLogger("mealie-mcp")


def register_labels_tools(mcp: FastMCP, mealie: MealieFetcher) -> None:
    """Register all label-related tools with the MCP server."""

    @mcp.tool()
    def get_labels(
        search: Optional[str] = None,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
    ) -> Dict[str, Any]:
        """List the group's labels, optionally filtered by a search term.

        Labels are the colored, group-wide organizers Mealie uses on foods
        and shopping-list items (e.g. "Produce", "Dairy"). Use this to
        resolve an existing label id+name before assigning it to a food.

        Args:
            search: Search term to filter labels by name.
            page: Page number to retrieve.
            per_page: Number of items per page.

        Returns:
            Dict[str, Any]: Labels (under "items") with pagination information.
        """
        try:
            logger.info(
                {"message": "Fetching labels", "search": search, "per_page": per_page}
            )
            return mealie.get_labels(search=search, page=page, per_page=per_page)
        except Exception as e:
            error_msg = f"Error fetching labels: {str(e)}"
            logger.error({"message": error_msg})
            logger.debug(
                {"message": "Error traceback", "traceback": traceback.format_exc()}
            )
            raise ToolError(error_msg)

    @mcp.tool()
    def create_label(name: str, color: Optional[str] = None) -> Dict[str, Any]:
        """Create a new group label.

        Args:
            name: Name of the label (e.g. "Produce").
            color: Optional hex color for the label (e.g. "#4CAF50").

        Returns:
            Dict[str, Any]: The created label.
        """
        try:
            logger.info({"message": "Creating label", "name": name})
            return mealie.create_label(name, color=color)
        except Exception as e:
            error_msg = f"Error creating label '{name}': {str(e)}"
            logger.error({"message": error_msg})
            logger.debug(
                {"message": "Error traceback", "traceback": traceback.format_exc()}
            )
            raise ToolError(error_msg)

    @mcp.tool()
    def get_label(label_id: str) -> Dict[str, Any]:
        """Get a specific label by ID.

        Args:
            label_id: The UUID of the label.

        Returns:
            Dict[str, Any]: The label details.
        """
        try:
            logger.info({"message": "Fetching label", "label_id": label_id})
            return mealie.get_label(label_id)
        except Exception as e:
            error_msg = f"Error fetching label '{label_id}': {str(e)}"
            logger.error({"message": error_msg})
            logger.debug(
                {"message": "Error traceback", "traceback": traceback.format_exc()}
            )
            raise ToolError(error_msg)

    @mcp.tool()
    def update_label(
        label_id: str,
        name: Optional[str] = None,
        color: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update a label's details (only provided fields are changed).

        Args:
            label_id: The UUID of the label to update.
            name: New name for the label.
            color: New hex color for the label.

        Returns:
            Dict[str, Any]: The updated label.
        """
        try:
            logger.info({"message": "Updating label", "label_id": label_id})

            label_data: Dict[str, Any] = {}
            if name is not None:
                label_data["name"] = name
            if color is not None:
                label_data["color"] = color

            if not label_data:
                raise ValueError("At least one field must be provided to update")

            return mealie.update_label(label_id, label_data)
        except Exception as e:
            error_msg = f"Error updating label '{label_id}': {str(e)}"
            logger.error({"message": error_msg})
            logger.debug(
                {"message": "Error traceback", "traceback": traceback.format_exc()}
            )
            raise ToolError(error_msg)

    @mcp.tool()
    def delete_label(label_id: str) -> Dict[str, Any]:
        """Delete a specific label.

        Args:
            label_id: The UUID of the label to delete.

        Returns:
            Dict[str, Any]: Confirmation of deletion.
        """
        try:
            logger.info({"message": "Deleting label", "label_id": label_id})
            return mealie.delete_label(label_id)
        except Exception as e:
            error_msg = f"Error deleting label '{label_id}': {str(e)}"
            logger.error({"message": error_msg})
            logger.debug(
                {"message": "Error traceback", "traceback": traceback.format_exc()}
            )
            raise ToolError(error_msg)
