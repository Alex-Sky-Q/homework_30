from typing import AsyncGenerator

from sqlalchemy import Column, ForeignKey, Integer, Table, Text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

DATABASE_URL = "sqlite+aiosqlite:///./recipes.db"

engine = create_async_engine(DATABASE_URL, echo=True)
# expire_on_commit=False will prevent attributes from being expired after commit.
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Верни сессию для работы с БД"""
    async with async_session() as session:
        yield session


class Base(DeclarativeBase):
    pass


# Таблица для связи рецептов и ингредиентов
recipe_ingredient_link = Table('recipe_ingredient', Base.metadata,
    Column('recipe_id', ForeignKey('recipe.id'), primary_key=True),
    Column('ingredient_id', ForeignKey('ingredient.id'), primary_key=True))


class Recipe(Base):
    """Модель рецепта"""
    __tablename__ = 'recipe'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    views: Mapped[int] = mapped_column(Integer, default=0)
    cook_time: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Связь с ингредиентами
    ingredients: Mapped[list["Ingredient"]] = relationship(secondary=recipe_ingredient_link, back_populates="recipes",
                                                           lazy="selectin")

    def __repr__(self):
        return f"<Recipe(id={self.id}, name='{self.name}')>"


class Ingredient(Base):
    """Модель ингредиента"""
    __tablename__ = 'ingredient'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    # Связь с рецептами
    recipes: Mapped[list["Recipe"]] = relationship(secondary=recipe_ingredient_link, back_populates="ingredients")

    def __repr__(self):
        return f"<Ingredient(id={self.id}, name='{self.name}')>"


