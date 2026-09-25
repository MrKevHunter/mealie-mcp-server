"""Tests for the food label tools (set_food_label, set_food_label_by_name)."""

import pytest
from mcp.server.fastmcp.exceptions import ToolError

# --- set_food_label -----------------------------------------------------------


async def test_set_food_label_assigns_label_id(invoke, fetcher):
    fetcher.foods = [{"id": "f1", "name": "Carrot", "aliases": []}]

    await invoke("set_food_label", food_id="f1", label_id="l1")

    req = fetcher.last("PUT", "/api/foods/f1")
    assert req["json"]["labelId"] == "l1"


async def test_set_food_label_can_clear(invoke, fetcher):
    fetcher.foods = [{"id": "f1", "name": "Carrot", "labelId": "l1", "aliases": []}]

    await invoke("set_food_label", food_id="f1")

    req = fetcher.last("PUT", "/api/foods/f1")
    assert req["json"]["labelId"] is None


async def test_set_food_label_validates_food_id(invoke, fetcher):
    with pytest.raises(ToolError):
        await invoke("set_food_label", food_id="", label_id="l1")


# --- set_food_label_by_name ----------------------------------------------------


async def test_set_food_label_by_name_resolves_existing_label(invoke, fetcher):
    fetcher.foods = [{"id": "f1", "name": "Carrot", "aliases": []}]
    fetcher.labels = [{"id": "l1", "name": "Produce", "color": "#4CAF50"}]

    await invoke("set_food_label_by_name", food_name="carrot", label_name="produce")

    req = fetcher.last("PUT", "/api/foods/f1")
    assert req["json"]["labelId"] == "l1"
    assert len(fetcher.labels) == 1


async def test_set_food_label_by_name_creates_missing_label(invoke, fetcher):
    fetcher.foods = [{"id": "f1", "name": "Carrot", "aliases": []}]

    result = await invoke(
        "set_food_label_by_name", food_name="Carrot", label_name="Produce"
    )

    assert len(fetcher.labels) == 1
    assert fetcher.labels[0]["name"] == "Produce"
    assert result["labelId"] == fetcher.labels[0]["id"]


async def test_set_food_label_by_name_errors_on_unknown_food(invoke, fetcher):
    with pytest.raises(ToolError):
        await invoke(
            "set_food_label_by_name", food_name="Nonexistent", label_name="Produce"
        )
