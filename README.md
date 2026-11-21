# Лабораторный проект

[![labs](https://github.com/entozhevlad/abds-labs/actions/workflows/energosbyt.lab.yml/badge.svg)](https://github.com/entozhevlad/abds-labs/actions/workflows/energosbyt.lab.yml)

Backend-сервис вымышленной ЖКХ-компании для практики по курсу
«Архитектура систем обработки больших данных».

## С чего начать

1. **‼️ Настройте репозиторий** — проведите обязательную настройку контрибьюторов
   и защиты ветки (см. ниже).
2. **[Лабораторные работы](https://github.com/sitnikovik/abds/tree/master/lab)** —
   технические задания для каждой лабораторной работы.
3. **[CONTRIBUTING.md](CONTRIBUTING.md)** — требования к структуре проекта,
   процесс разработки и проверки.
4. **[Документация курса](https://github.com/sitnikovik/abds)** — методические
   материалы и дополнительные ресурсы.

## Лабораторная №1

HTTP-сервис на Python 3.12 и FastAPI с ClickHouse 26.7. Зависимостями управляет
uv, конфигурация хранится в `.env.local`.

## Запуск

Нужны Docker Compose и Make.

```sh
make run       # запустить ClickHouse и приложение
make setup     # создать схему, сгенерировать и загрузить данные
curl -i http://localhost:8080/ping
make stop
```

Дополнительные команды:

```sh
make gen       # создать CSV в data/
make load      # создать недостающие таблицы и загрузить CSV
make teardown  # удалить таблицы лабораторной
make test      # модульные тесты
make check     # интеграционные тесты после run и setup
make lint      # Ruff
make mypy      # строгая проверка типов
```

Повторная загрузка в непустую базу отклоняется. Для полной перезагрузки выполните
`make teardown && make setup`. Папки `data/` и `volume/` не добавляются в Git.
Swagger доступен по адресу `http://localhost:8080/docs`. Примеры запросов также
находятся в `api/energosbyt.postman_collection.json`.

## Данные

Генератор создаёт 1000 объектов, 1000 собственников, 1100 счётчиков, две версии
тарифа, 36 000 счетов и показания за период 2023-11-01—2026-10-31. Около 3%
показаний имеют корректировку. У 100 объектов счётчик заменяется.

| Таблица | Движок | ORDER BY | PARTITION BY |
| --- | --- | --- | --- |
| `dim_realty` | MergeTree | `id` | — |
| `dim_gauges` | MergeTree | `id` | — |
| `dim_tariffs` | ReplacingMergeTree | `(id, valid_from)` | — |
| `dim_users` | ReplacingMergeTree | `id` | — |
| `fact_gauge_bindings` | VersionedCollapsingMergeTree | `(realty_id, gauge_id)` | — |
| `fact_meter_readings` | ReplacingMergeTree | `(realty_id, reading_date)` | месяц показания |
| `fact_invoice` | MergeTree | `(realty_id, created_at)` | месяц выставления |

Измерения небольшие и читаются по идентификатору, поэтому не партиционируются.
Показания и счета партиционируются по месяцу для ограничения чтения по периоду.
Ключ показаний содержит объект и дату, поэтому корректировка заменяет прежнюю
версию независимо от собственника, тарифа или счётчика. Ключ привязки позволяет
схлопнуть установку и её аннулирование с одинаковой версией.

## Проверка SCD

[Сценарии проверки SCD](docs/scd.md).

## Настройка репозитория

### Защита основной ветки

После создания репозитория из шаблона **обязательно настройте правила защиты
для ветки `main`**:

1. Откройте **Settings** → **Branches** → **Add classic branch protection rule**.
2. В поле **Branch name pattern** укажите: `main`.
3. Включите следующие опции:
   - **Require a pull request before merging**
     - Require approvals: **1**: требует минимум одного одобрения перед слиянием.
   - **Require status checks to pass before merging**
     - Выберите `autograder`: проверит все лабораторные работы автоматически.
     - **Require branches to be up to date before merging** (рекомендуется):
       требует, чтобы ветка PR была синхронизирована с последними изменениями
       из основной ветки перед слиянием.
   - **Do not allow bypassing the above settings**: запрещает обход настроек
     защиты ветки.
4. Нажмите **Create** или **Save changes**.

> ⚠️ **Важно:** Без этих настроек автоматические проверки не будут блокировать
> PR с ошибками.

### Добавление коллабораторов

Чтобы преподаватели могли проводить код-ревью:

1. Откройте **Settings** → **Collaborators**.
2. Нажмите **Add people**.
3. Добавьте всех, кто есть в списке ревьюеров в файле [CODEOWNERS](CODEOWNERS).
4. Выберите роль **Write** (или выше), иначе ревьюер не сможет одобрить PR.

## Помощь

Возникли вопросы? → [@sitnikovik](https://t.me/sitnikovik)
