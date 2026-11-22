# Проверка SCD

SQL выполняется так:

```sh
docker compose --env-file .env.local exec clickhouse \
  clickhouse-client --database energosbyt
```

### SCD 1 и SCD 3

```sh
curl -X PATCH localhost:8080/users/1 \
  -H 'Content-Type: application/json' \
  -d '{"fio":"Петрова Анна Сергеевна","phone":"+79111111111"}'
curl -X PATCH localhost:8080/users/1 \
  -H 'Content-Type: application/json' \
  -d '{"phone":"+79222222222"}'
```

```sql
SELECT id, fio, phone, phone_prev
FROM dim_users FINAL
WHERE id = 1;

SELECT count()
FROM dim_users FINAL
WHERE id = 1 AND fio = 'Иванов Иван 1';
```

Первый запрос показывает новое ФИО, последний телефон и предыдущий телефон.
Второй возвращает `0`: с `FINAL` видно только актуальное ФИО по SCD 1.

### SCD 2 и старый счёт

```sql
SELECT id, price_day_kwph, price_night_kwph, valid_from, valid_to
FROM dim_tariffs FINAL
ORDER BY valid_from;

SELECT i.created_at, i.price,
       toUInt64(i.day_kw) * t.price_day_kwph
       + toUInt64(i.night_kw) * t.price_night_kwph AS expected_price
FROM fact_invoice AS i
INNER JOIN (SELECT * FROM dim_tariffs FINAL) AS t
    ON i.tariff_id = t.id
WHERE i.realty_id = 1
  AND i.created_at >= t.valid_from
  AND i.created_at < t.valid_to
ORDER BY i.created_at;
```

Первый запрос показывает интервалы версий тарифа. Второй подтверждает, что каждый
счёт рассчитан по тарифу, действовавшему на дату его создания.

### Корректировка показания

```sh
curl -X POST localhost:8080/realty/1/readings \
  -H 'Content-Type: application/json' \
  -d '{"user_id":1,"gauge_id":1,"tariff_id":1,"reading_date":"2026-10-01","day_kw":1250,"night_kw":300}'
curl -X POST localhost:8080/realty/1/readings \
  -H 'Content-Type: application/json' \
  -d '{"user_id":1,"gauge_id":1,"tariff_id":1,"reading_date":"2026-10-01","day_kw":1255,"night_kw":301}'
```

```sql
SELECT *
FROM fact_meter_readings FINAL
WHERE realty_id = 1 AND reading_date = '2026-10-01';
```

Запрос возвращает одну актуальную строку со значениями `1255` и `301`.

### Замена счётчика

```sh
curl -X POST localhost:8080/realty/1/gauges \
  -H 'Content-Type: application/json' \
  -d '{"gauge_id":2}'
```

```sql
SELECT *
FROM fact_gauge_bindings FINAL
WHERE realty_id = 1;
```

После схлопывания остаётся новая активная установка с увеличенной версией.

### Удаление ошибочной строки

```sql
INSERT INTO fact_invoice VALUES
(999999, 1, 1, 1, 100, 20, 670000, '2026-11-10', '2026-10-31 23:00:00');

ALTER TABLE fact_invoice DELETE
WHERE realty_id = 999999
SETTINGS mutations_sync = 1;

SELECT count()
FROM fact_invoice
WHERE realty_id = 999999;
```

Последний запрос возвращает `0`.
