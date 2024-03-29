"""Конфигурация приложения."""
import logging
import os
from logging import config as logging_config
from pathlib import Path

from pydantic import BaseModel, BaseSettings, Field

from core.logger import LOGGING

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class PaymentService(BaseSettings):
    url: str


class UsersApp(BaseModel):
    jwt_secret_key: str = Field("someword")
    algorithm: str = Field("HS256")
    psw_hash_iterations: int = Field(1000)
    salt_length: int = Field(20)
    kdf_algorithm: str = Field("p5k2")


class Postgres(BaseSettings):
    host: str = Field("127.0.0.1")
    port: int = Field(5432)
    db: str = Field("movies_database")
    user: str = Field("app")
    password: str = Field("123qwe")


class Settings(BaseSettings):
    users_app: UsersApp = Field(UsersApp())
    postgres: Postgres = Field(Postgres)
    paymentservice: PaymentService = Field(PaymentService)
    project_name: str = Field("billing")
    debug: bool = Field(False)

    class Config:
        env_file = BASE_DIR.joinpath(".env")
        env_nested_delimiter = "__"


settings = Settings()

if settings.debug:
    LOGGING["root"]["level"] = "DEBUG"

logging_config.dictConfig(LOGGING)
logging.debug("%s", os.environ)

logging.debug("%s", settings.dict())
