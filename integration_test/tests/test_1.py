import logging
import time

import allure
from allure import step

from core.config import settings


@allure.suite("Интеграционные тесты")
@allure.title("Проверка оплаты пользователем")
def test_1(db_session, initial_data, billing_client, send_telegram_notify):
    product, movies = initial_data
    with step("Получение списка доступных продуктов"):
        assert billing_client.get_products(), billing_client.last_error
        assert len(billing_client.last_json), "Ожидается один продукт"
        subscribed_product = billing_client.last_json[0]

    with step("Проверка отсутствия прав у пользователя на просмотр фильма"):
        assert billing_client.get_rights(movie_id=movies[0].id), billing_client.last_error
        assert not billing_client.last_json["allow"], "У пользователя есть права на просмотр фильма"

    with step("Запрос пользователем на покупку подписки"):
        assert billing_client.add_product_to_user(product_id=subscribed_product["id"]), billing_client.last_error
        assert "url" in billing_client.last_json, "В ответе отсутствует ссылка на оплату"
        checkout_url = billing_client.last_json["url"]

    with step("Проверка отсутствия прав у пользователя на просмотр фильма после оформления подписки"):
        assert billing_client.get_rights(movie_id=movies[0].id), billing_client.last_error
        assert not billing_client.last_json["allow"], "У пользователя есть права на просмотр фильма"

    with step("Ожидание оплаты подписки пользователем в течении 2-х минут"):
        if not settings.debug:
            send_telegram_notify(f"Необходимо произвести оплату по ссылке\n{checkout_url}")
        logging.info(f"Необходимо произвести оплату по ссылке\n{checkout_url}")
        start_time = time.time()
        while time.time() < start_time + 120:
            billing_client.get_payments()
            if billing_client.last_json["items"][0]["pay_date"]:
                break
            time.sleep(10)
        else:
            assert False, "За две минуты не было получено подтверждение об оплате"
        id_payment = billing_client.last_json["items"][0]["id"]

    with step("Проверка успешного доступа к контенту после оформления подписки"):
        assert billing_client.get_rights(movie_id=movies[0].id), billing_client.last_error
        assert billing_client.last_json["allow"], "У пользователя нет прав на просмотр фильма"

    with step("Отмена платежа"):
        assert billing_client.cancel_payment(payment_id=id_payment), billing_client.last_error

    with step("Проверка отсутствия прав у пользователя на просмотр фильма"):
        assert billing_client.get_rights(movie_id=movies[0].id), billing_client.last_error
        assert not billing_client.last_json["allow"], "У пользователя есть права на просмотр фильма"
