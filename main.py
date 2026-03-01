from collections.abc import Sequence
from contextlib import asynccontextmanager

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import asc, desc, select 
from sqlalchemy.ext.asyncio import AsyncSession

from db import Base, Ingredient, Recipe, engine, get_session
import schemas


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Инициализация и завершение работы приложения"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(title="Recipe API", description="Асинхронный сервис для управления рецептами", lifespan=lifespan)


@app.get("/recipes", response_model=list[schemas.RecipeSchema], summary="Получить список всех рецептов")
async def get_recipes(session: AsyncSession = Depends(get_session)) -> Sequence[Recipe]:
    """Верни список всех рецептов, отсортированных по популярности. Сортировка:
    1. По убыванию количества просмотров (views)
    2. По возрастанию времени готовки (cook_time)

    :param session: Асинхронная сессия БД
    """
    query = select(Recipe).order_by(desc(Recipe.views), asc(Recipe.cook_time))
    result = await session.execute(query)
    return result.scalars().all()


@app.get("/recipes/{recipe_id}", response_model=schemas.RecipeDetailed, summary="Получить информацию о рецепте")
async def get_recipe(recipe_id: int, session: AsyncSession = Depends(get_session)):
    """Верни информацию о рецепте по его ID, включая ингредиенты

    :param recipe_id: Уникальный идентификатор рецепта
    :param session: Асинхронная сессия БД
    """
    recipe = await session.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Recipe with id {recipe_id} not found")

    recipe.views += 1
    await session.commit()
    await session.refresh(recipe)
    return recipe


@app.post("/recipes", response_model=schemas.RecipeOut, summary="Добавить новый рецепт",
          status_code=status.HTTP_201_CREATED)
async def create_recipe(recipe_data: schemas.RecipeIn, session: AsyncSession = Depends(get_session)) -> Recipe:
    """Создай новый рецепт с указанными параметрами и ингредиентами.

    :param recipe_data: Данные нового рецепта
    :param session: Асинхронная сессия БД
    """
    new_recipe = Recipe(name=recipe_data.name, cook_time=recipe_data.cook_time, description=recipe_data.description)
    if recipe_data.ingredients:
        # Ищем все существующие ингредиенты
        query = select(Ingredient).where(Ingredient.name.in_(recipe_data.ingredients))
        result = await session.execute(query)
        existing_ingredients = {ing.name: ing for ing in result.scalars().all()}
        # Распределяем: существующие берем из словаря, новые создаем
        for ing_name in recipe_data.ingredients:
            if ing_name in existing_ingredients:
                ingredient = existing_ingredients[ing_name]
            else:
                ingredient = Ingredient(name=ing_name)
                session.add(ingredient)
            new_recipe.ingredients.append(ingredient)
    session.add(new_recipe)
    await session.commit()
    await session.refresh(new_recipe)
    return new_recipe


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
