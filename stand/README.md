# Тренировочный стенд: DWH (PostgreSQL) + Airflow + Superset

Локальный стенд для отработки связки перед разворотом на ВМ компании. Здесь можно безопасно разобраться, как системы работают вместе, написать и отладить DAG загрузки Excel, собрать первые отчёты.

**Это не production-конфигурация.** Что менять для боевого контура, написано в конце.

## Что внутри

| Сервис | Назначение | Адрес после запуска |
|---|---|---|
| PostgreSQL 16 | БД DWH (`dwh`) и служебные БД Airflow и Superset | `127.0.0.1:5432` |
| Airflow 2.10.5 | Оркестрация ETL | http://127.0.0.1:8081 |
| Superset 5.0.0 | Отчёты и дашборды | http://127.0.0.1:8088 |
| Redis 7 | Кеш Superset | внутри сети Docker |

ELMA365 в стенд не входит: это коммерческий продукт, он ставится по документации вендора.

Слои DWH: `raw` (как пришло из источника) → `core` (проверенные данные) → `mart` (витрины для отчётов).
Роли: `dwh_loader` (пишет, используется Airflow), `dwh_reader` (только чтение `core` и `mart`, используется Superset).

## Структура

```
.
├── docker-compose.yml
├── .env.example                  # шаблон секретов (сам .env в Git не попадает)
├── postgres/init/01-init.sh      # БД, роли, схемы и таблицы DWH
├── airflow/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── dags/
│       ├── excel_to_dwh.py       # DAG: Excel -> raw -> core
│       └── etl/excel_validation.py   # чтение и проверка Excel
├── superset/superset_config.py
├── scripts/make_sample_xlsx.py   # тестовые Excel-файлы
├── data/inbox/                   # сюда кладутся Excel (аналог сетевой папки)
└── docs/questions-it-ib.md       # вопросы к центральному IT и ИБ
```

## Быстрый старт

Нужны Docker и Docker Compose v2.

```bash
cp .env.example .env
# Откройте .env и замените все значения change_me_*
# На Linux поставьте AIRFLOW_UID=$(id -u) (то есть ваш UID, число)

docker compose up -d --build
docker compose ps          # дождитесь, пока сервисы станут healthy / running
```

Первый запуск занимает несколько минут: собираются образы и применяются миграции.

Если нужно начать с чистого листа (init-скрипт Postgres выполняется только при создании тома):

```bash
docker compose down -v
```

## Проверка ETL

```bash
pip install pandas openpyxl
python scripts/make_sample_xlsx.py     # создаст sales_good.xlsx и sales_bad.xlsx в data/inbox
```

1. Откройте Airflow, включите DAG `excel_to_dwh` и запустите вручную (кнопка Trigger).
2. `sales_good.xlsx` должен уйти в `data/inbox/archive/`, а `sales_bad.xlsx` в `data/inbox/rejected/`.
3. Проверьте результат:

```bash
docker compose exec postgres psql -U postgres -d dwh -c "SELECT * FROM raw.load_log;"
docker compose exec postgres psql -U postgres -d dwh -c "SELECT * FROM mart.sales_by_branch_month;"
```

В `raw.load_log` у отклонённого файла будет сообщение с номерами плохих строк Excel.

## Подключение Superset к DWH

В Superset: **Settings → Database Connections → + Database → PostgreSQL**, затем SQLAlchemy URI:

```
postgresql+psycopg2://dwh_reader:<DWH_READER_PASSWORD>@postgres:5432/dwh
```

Хост `postgres` работает внутри сети Docker. Читатель видит только `core` и `mart`. Дальше: **Datasets → + Dataset**, выберите `mart.sales_by_branch_month` и стройте графики.

## Отправка в Git

Стенд лежит в папке `stand/` общего репозитория `data-platform-stack`. Коммитьте и пушьте из корня репозитория, а не из этой папки.

## Что поменять для боевого контура

- **Раздельные ВМ** под DWH, Airflow и Superset; у Airflow и Superset свои metadata-БД, не в DWH. Здесь для простоты всё в одном экземпляре PostgreSQL.
- **Закрытый контур:** образы и пакеты из внутреннего реестра (Harbor/Nexus) и зеркала PyPI, версии зафиксированы. Образы: `apache/airflow`, `apache/superset`, `postgres`, `redis`.
- **TLS** через nginx с сертификатом корпоративного CA; порты не публиковать наружу, кроме 443.
- **Аутентификация** через AD/LDAP (Airflow и Superset это поддерживают).
- **Секреты** не в `.env`, а в Ansible Vault или корпоративном Vault.
- **Excel-папка:** монтирование шары по CIFS/SMB сервисной учёткой с правами на чтение; обработанные файлы переносить в отдельный каталог с правом записи.
- **Бэкапы** PostgreSQL (например, pgBackRest) с проверкой восстановления, мониторинг и алерты на падение DAG-ов.
- **Airflow:** `LocalExecutor` подходит для небольших нагрузок. Версию 2.10 обсудите с IT: есть более новая линия 3.x, у неё другая схема компонентов.
- **Superset:** `TALISMAN_ENABLED` и `SESSION_COOKIE_SECURE` включить при работе по HTTPS.

## Известные упрощения DAG-а

- `core.sales` пересобирается целиком из `raw` при каждой загрузке. Для небольших объёмов это просто и надёжно, для больших нужен инкремент.
- Файл с ошибкой отклоняется целиком (частичная загрузка не делается намеренно).
- Файл с тем же именем заменяет ранее загруженные данные этого файла.
