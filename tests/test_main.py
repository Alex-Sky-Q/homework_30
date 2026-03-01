from httpx import AsyncClient


async def test_get_recipes_empty(client: AsyncClient):
    """GET /recipes — пустой список"""
    response = await client.get("/recipes")
    assert response.status_code == 200
    assert response.json() == []


async def test_create_recipe(client: AsyncClient):
    """POST /recipes — создание рецепта"""
    recipe_data = {
        "name": "Борщ",
        "cook_time": 110,
        "description": "Классический борщ",
        "ingredients": ["свёкла", "капуста", "картофель"],
    }
    response = await client.post("/recipes", json=recipe_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Борщ"
    assert data["description"] == "Классический борщ"
    assert data["cook_time"] == 110
    assert len(data["ingredients"]) == 3
    assert "id" in data


async def test_get_recipe_by_id(client: AsyncClient):
    """GET /recipes/{id} — получение рецепта"""
    recipe_data = {
        "name": "Паста",
        "cook_time": 15,
        "description": "Быстрая паста",
        "ingredients": ["макароны"],
        }
    create_resp = await client.post("/recipes", json=recipe_data)
    recipe_id = create_resp.json()["id"]
    response = await client.get(f"/recipes/{recipe_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Паста"
    assert data["description"] == "Быстрая паста"
    assert data["cook_time"] == 15
    assert len(data["ingredients"]) == 1


async def test_get_recipe_not_found(client: AsyncClient):
    """GET /recipes/{id} — рецепт не найден"""
    response = await client.get("/recipes/99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
