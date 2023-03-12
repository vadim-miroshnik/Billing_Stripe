import datetime

from pydantic import BaseModel


class BillingMovies(BaseModel):
    """
    Модель фильмов для запроса в бд постгреса
    """

    id: str
    name: str
    description: str = None


class BillingProduct(BaseModel):
    """
    Модель фильмов для запроса в бд постгреса
    """

    id: str
    name: str
    price: int
    duration: str
