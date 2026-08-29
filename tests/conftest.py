"""Shared test fixtures.

Tests exercise the MCP tools end-to-end against a fake Mealie client that
records the HTTP requests the mixins would make (method, url, json, params)
and returns canned responses. No network access is required.
"""

import os
import sys

import pytest
from mcp.server.fastmcp import FastMCP

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mealie import MealieFetcher  # noqa: E402
from tools import register_all_tools  # noqa: E402

# A minimal but schema-valid recipe payload (satisfies the required Recipe
# fields), used as the response to GET /api/recipes/<slug>.
BASE_RECIPE = {
    "id": "00000000-0000-0000-0000-000000000000",
    "userId": "11111111-1111-1111-1111-111111111111",
    "householdId": "22222222-2222-2222-2222-222222222222",
    "groupId": "33333333-3333-3333-3333-333333333333",
    "name": "Test Recipe",
    "slug": "test-recipe",
    "dateAdded": "2024-01-01",
    "dateUpdated": "2024-01-01T00:00:00",
    "createdAt": "2024-01-01T00:00:00",
    "updatedAt": "2024-01-01T00:00:00",
}


class FakeFetcher(MealieFetcher):
    """MealieFetcher with the network layer replaced by a recorder.

    Skips MealieClient.__init__ (no connection) and overrides _handle_request
    so the real mixin methods run and we can assert on the requests they build.
    """

    def __init__(self):
        self.requests = []
        self.created_slug = "test-recipe"
        self.recipe = dict(BASE_RECIPE)
        self.tags = []
        self.foods = []

    def _handle_request(self, method, url, **kwargs):
        self.requests.append(
            {
                "method": method,
                "url": url,
                "json": kwargs.get("json"),
                "params": kwargs.get("params"),
            }
        )
        if method == "POST" and url == "/api/recipes":
            name = (kwargs.get("json") or {}).get("name")
            if name:
                # reflect the created name on subsequent GET (like the real API)
                self.recipe = {**self.recipe, "name": name, "slug": self.created_slug}
            return self.created_slug
        if method == "GET" and url.startswith("/api/recipes/") and url.count("/") == 3:
            return dict(self.recipe)
        if method in ("PUT", "PATCH") and url.startswith("/api/recipes/"):
            return kwargs.get("json", {})
        if method == "GET" and url == "/api/users/self":
            return {
                "id": "user-1",
                "householdId": "household-1",
                "email": "test@example.com",
            }
        # single-record GET (the fetch-merge update path reads the existing record)
        if method == "GET" and url.startswith("/api/foods/"):
            food_id = url.rsplit("/", 1)[-1]
            existing = next((f for f in self.foods if f["id"] == food_id), None)
            if existing is not None:
                return dict(existing)
            return {
                "id": food_id,
                "name": "Existing",
                "pluralName": "Existings",
                "description": "old",
                "householdsWithIngredientFood": [],
                "aliases": [],
            }
        if method == "GET" and (
            url.startswith("/api/units/") or url.startswith("/api/organizers/tools/")
        ):
            return {
                "id": url.rsplit("/", 1)[-1],
                "name": "Existing",
                "pluralName": "Existings",
                "description": "old",
            }
        if method == "GET" and url.startswith("/api/organizers/categories/"):
            item_id = url.rsplit("/", 1)[-1]
            return {"id": item_id, "name": "Category", "slug": "category"}
        if method == "GET" and url.startswith("/api/organizers/tags/"):
            item_id = url.rsplit("/", 1)[-1]
            return {"id": item_id, "name": "Tag", "slug": "tag"}
        if method == "GET" and url == "/api/organizers/tags":
            search = (kwargs.get("params") or {}).get("search")
            items = self.tags
            if search:
                items = [t for t in items if search.lower() in t["name"].lower()]
            return {"items": items, "page": 1, "perPage": 50, "total": len(items)}
        if method == "POST" and url == "/api/organizers/tags":
            name = (kwargs.get("json") or {}).get("name")
            tag = {
                "id": f"tag-{len(self.tags) + 1}",
                "name": name,
                "slug": name.lower().replace(" ", "-"),
            }
            self.tags.append(tag)
            return tag
        if method == "GET" and url.startswith("/api/households/mealplans/"):
            return {
                "id": url.rsplit("/", 1)[-1],
                "groupId": "group-1",
                "userId": "user-1",
                "date": "2026-07-12",
                "entryType": "dinner",
                "title": "Existing meal",
            }
        if method == "GET" and url.startswith("/api/households/shopping/lists/"):
            return {
                "id": url.rsplit("/", 1)[-1],
                "groupId": "group-1",
                "userId": "user-1",
                "name": "Existing list",
            }
        # foods list/create are backed by an in-memory store so search/match
        # flows (e.g. set_foods_on_hand_by_name) can be exercised end-to-end
        if method == "GET" and url == "/api/foods":
            search = (kwargs.get("params") or {}).get("search")
            items = self.foods
            if search:
                items = [f for f in items if search.lower() in f["name"].lower()]
            return {"items": items, "page": 1, "perPage": 50, "total": len(items)}
        if method == "POST" and url == "/api/foods":
            payload = kwargs.get("json") or {}
            food = {
                **payload,
                "id": f"food-{len(self.foods) + 1}",
                "householdsWithIngredientFood": [],
            }
            self.foods.append(food)
            return food
        if method == "PUT" and url.startswith("/api/foods/"):
            food_id = url.rsplit("/", 1)[-1]
            updated = kwargs.get("json", {})
            for i, f in enumerate(self.foods):
                if f["id"] == food_id:
                    self.foods[i] = updated
                    break
            return updated
        # list endpoints
        if method == "GET" and url in (
            "/api/units",
            "/api/organizers/tools",
        ):
            return {
                "items": [{"id": "x1", "name": "Sample"}],
                "page": 1,
                "perPage": 50,
                "total": 1,
            }
        # create echoes the body with a generated id
        if method == "POST" and url in (
            "/api/units",
            "/api/organizers/tools",
        ):
            return {**(kwargs.get("json") or {}), "id": "generated-0001"}
        # full-replace update echoes the merged body
        if method == "PUT" and (
            url.startswith("/api/units/") or url.startswith("/api/organizers/tools/")
        ):
            return kwargs.get("json", {})
        # delete (Mealie normalizes the empty body to a success payload)
        if method == "DELETE":
            return {"success": True, "message": "Operation completed successfully"}
        return {"ok": True}

    def last(self, method=None, url_contains=None):
        """Return the most recent recorded request matching method/url filter."""
        for req in reversed(self.requests):
            if method is not None and req["method"] != method:
                continue
            if url_contains is not None and url_contains not in req["url"]:
                continue
            return req
        return None


@pytest.fixture
def fetcher():
    return FakeFetcher()


@pytest.fixture
def server(fetcher):
    mcp = FastMCP("test")
    register_all_tools(mcp, fetcher)
    return mcp, fetcher


@pytest.fixture
def invoke(server):
    """Async helper: call a tool by name with kwargs, return its parsed result."""
    import json

    mcp, _ = server

    async def _invoke(tool_name, /, **arguments):
        result = await mcp.call_tool(tool_name, arguments)
        content, structured = result if isinstance(result, tuple) else (result, None)
        if isinstance(structured, dict) and set(structured.keys()) == {"result"}:
            return structured["result"]
        if structured is not None:
            return structured
        if content and getattr(content[0], "text", None):
            return json.loads(content[0].text)
        return content

    return _invoke
