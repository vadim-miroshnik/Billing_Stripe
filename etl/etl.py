import datetime
import logging

import psycopg2
from psycopg2.extensions import connection as pg_connection
from pydantic import ValidationError
from psycopg2.extras import execute_batch
from config import settings


class PostgresExtractor:
    """
    Порционное получение актуальных данных по фильмам из БД
    """

    def __init__(self, connect: pg_connection, last_time=None):
        """
        :param connect: Соединение с базой Postgress
        """
        self.connect = connect
        self.last_time = last_time if last_time else datetime.datetime.min
        self.limit = settings.fetch_limit

    def get_server_datetime(self) -> datetime.datetime:
        """
        Получение текущего времени сервера Postgress
        :return:
        """
        with self.connect.cursor() as cursor:
            cursor.execute("select now();")
            data = cursor.fetchall().pop()
        logging.debug("Expose last time: %s", data[0])
        return data[0]

    def get_updated(self, query_executor, validator):
        offset = 0
        while True:
            with self.connect.cursor() as cursor:
                cursor.execute(query_executor(last_time=self.last_time, limit=self.limit, offset=offset))
                try:
                    models_list = [validator(**dict(row)) for row in cursor.fetchall()]
                except ValidationError as error:
                    logging.exception("%s", error)
                    raise error
            if not models_list:
                break
            logging.debug(f"Получено записей - %s", {len(models_list)})
            yield models_list
            offset = offset + self.limit


class PostgresLoader:
    def __init__(self, connect: pg_connection):
        self.connect = connect

    def save_all_data(self, db: str, inserted_data):
        # Получаем список имен полей для вставки
        fields_name_list = [key for key in inserted_data[0].dict()]
        # Переформатируется список полей в строку в формат sql
        fields_name_str = ", ".join([key for key in fields_name_list])
        fields_name_str_with_exclude = ", ".join([f"EXCLUDED.{key}" for key in fields_name_list])
        # Генерим строку по количеству элементов для вставки из %s для формата sql
        amount_values_str = ", ".join("%s" for _ in range(len(fields_name_list)))
        # Список из объектов данных
        inserted_data_list = [tuple(values_row.dict().values()) for values_row in inserted_data]
        logging.debug(inserted_data_list)
        with self.connect.cursor() as cursor:
            try:
                execute_batch(
                    cursor,
                    f"""INSERT INTO {db}({fields_name_str}) VALUES({amount_values_str}) 
                            ON CONFLICT (id) 
                            DO UPDATE SET ({fields_name_str}) = ({fields_name_str_with_exclude});""",
                    inserted_data_list,
                    page_size=settings.fetch_limit,
                )
            except (Exception, psycopg2.DatabaseError) as error:
                logging.exception(error)
                raise error
        logging.info(f"Обработано '{len(inserted_data_list)}' записей таблицы '{db}'")

    def commit_data(self):
        self.connect.commit()
