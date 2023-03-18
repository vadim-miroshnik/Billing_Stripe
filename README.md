# Биллинг. Проектная работа дипломного сервиса

https://github.com/dimkaddi/graduate_work

Для проверки взаимодействия между сервисами разработан интеграционный тест, 
позволяющий провести типовые операции, которые делает пользователь во время покупки подписки
на фильмы.

Тест включает в себя следующие этапы:

- Заполнение базы данных тестовыми данными - фильмы и подписка
- Авторизация пользователя для получения токена для дальнейшего взаимодействия с сервисом
- Получение списка продуктов на которые можно оформить подписку
- Проверка отсутствия доступа к контенту
- Оформление подписки и получение ссылку на оплату
- Ожидание оплаты
- Проверка успешного доступа к контенту
- Отмена оплаты за подписку
- Проверка отсутствия доступа к контенту

Оплата производится вручную и её необходимо сделать в течении двух минут после запуска тестов
по ссылке, которая отправляется тестами в телеграм.

### Запуск
Необходимо скопировать .env.example в .env, который располагается в корне проекта
При необходимости поменять значение для TELEGRAM__CHAT, чтобы выбрать свой чат для уведомления

    cp .env.example .env

Запуск теста осуществляется командой

    make run_test_service

После чего будет поднято тестовое окружение со специально выделенной для тестов базой данных.

Тесты дождутся запуска тестируемых сервисов.
Заполнят бд тестовыми данным. 
И проведут тестирование.

Во время тестирования необходимо совершить оплату по предложенной ссылке.
В качестве платежной карты следует использовать карту с номером:
    
    4242 4242 4242 4242

Остальные реквизиты карты можно вводить любые.

Тесты должны пройти успешно
```
integration_test  | ============================= test session starts ==============================
integration_test  | platform linux -- Python 3.10.8, pytest-7.2.2, pluggy-1.0.0
integration_test  | rootdir: /opt/app
integration_test  | plugins: anyio-3.6.2, allure-pytest-2.13.1
integration_test  | collected 1 item
integration_test  | 
integration_test  | tests/test_1.py .                                                        [100%]
integration_test  | 
integration_test  | ============================== 1 passed in 47.68s ==============================
integration_test exited with code 0

```

## Компоненты системы

### Админская панель
Позволяет менеджерам онлайн-кинотеатра вносить фильмы и создавать продукты в виде подписок на фильмы

Запуск

    make run_admin_panel_service

Опенапи доступно по ссылке http://127.0.0.1:8000/

### Биллинговый сервис
Позволяет пользователям просматривать продукты, доступные для подписки, оформлять и отменять подписки,
оплачивать и отменять оплату подписок, просматривать выписку.

Запуск

    make run_billing_service

Админка доступна по ссылке http://127.0.0.1:8001/admin после запуска

### Сервис оплаты
Является 

    make run_pay-api_service

Swagger доступен по ссылке http://127.0.0.1:8002/apidocs/

### ETL
Вспомогательный сервис. Который вносит в бд биллинга информацию о продуктах и фильмах, 
созданных менеджерами онлайн-кинотеатра в панели администратора.

    make run_etl_service

```
etl  | 2023-03-18 10:59:54,216 - root - INFO - Обработано '1' записей таблицы 'movie'
etl  | 2023-03-18 10:59:54,220 - root - INFO - Обработано '1' записей таблицы 'product'
etl  | 2023-03-18 10:59:54,224 - root - INFO - Обработано '1' записей таблицы 'product_movie_link'
etl  | 2023-03-18 10:59:54,227 - root - INFO - Сохранено состояние 2023-03-18 10:59:54.205719+00:00
```

## Описание взаимодействия
Схема https://github.com/dimkaddi/graduate_work/blob/main/architecture/components.md
