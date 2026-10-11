#!/bin/bash
# Выполняется один раз при первом создании тома PostgreSQL.
# Создаёт служебные БД (airflow, superset), БД dwh, роли и слои схем.
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres <<EOSQL
CREATE ROLE airflow LOGIN PASSWORD '${AIRFLOW_DB_PASSWORD}';
CREATE DATABASE airflow OWNER airflow;

CREATE ROLE superset LOGIN PASSWORD '${SUPERSET_DB_PASSWORD}';
CREATE DATABASE superset OWNER superset;

-- Роли DWH: загрузчик (пишет) и читатель (для Superset и аналитиков)
CREATE ROLE dwh_loader LOGIN PASSWORD '${DWH_LOADER_PASSWORD}';
CREATE ROLE dwh_reader LOGIN PASSWORD '${DWH_READER_PASSWORD}';
CREATE DATABASE dwh OWNER dwh_loader;
REVOKE ALL ON DATABASE dwh FROM PUBLIC;
GRANT CONNECT ON DATABASE dwh TO dwh_loader, dwh_reader;
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname dwh <<'EOSQL'
-- Слои: raw (как пришло) -> core (очищенные данные) -> mart (витрины для отчётов)
REVOKE ALL ON SCHEMA public FROM PUBLIC;

CREATE SCHEMA raw  AUTHORIZATION dwh_loader;
CREATE SCHEMA core AUTHORIZATION dwh_loader;
CREATE SCHEMA mart AUTHORIZATION dwh_loader;

-- Читатель видит только core и mart, raw ему не нужен
GRANT USAGE ON SCHEMA core, mart TO dwh_reader;
ALTER DEFAULT PRIVILEGES FOR ROLE dwh_loader IN SCHEMA core GRANT SELECT ON TABLES TO dwh_reader;
ALTER DEFAULT PRIVILEGES FOR ROLE dwh_loader IN SCHEMA mart GRANT SELECT ON TABLES TO dwh_reader;

-- Объекты создаём от имени загрузчика, чтобы он был их владельцем
SET ROLE dwh_loader;

CREATE TABLE raw.sales_excel (
    id          bigserial PRIMARY KEY,
    source_file text          NOT NULL,
    row_num     integer       NOT NULL,   -- номер строки в Excel
    sale_date   date          NOT NULL,
    branch      text          NOT NULL,
    product     text,
    amount      numeric(14,2) NOT NULL,
    loaded_at   timestamptz   NOT NULL DEFAULT now()
);
CREATE INDEX ON raw.sales_excel (source_file);

-- Журнал загрузок: успехи и отклонённые файлы
CREATE TABLE raw.load_log (
    id          bigserial PRIMARY KEY,
    source_file text        NOT NULL,
    status      text        NOT NULL CHECK (status IN ('loaded', 'rejected')),
    rows_loaded integer     NOT NULL DEFAULT 0,
    message     text,
    logged_at   timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE core.sales (
    sale_date   date          NOT NULL,
    branch      text          NOT NULL,
    product     text,
    amount      numeric(14,2) NOT NULL,
    source_file text          NOT NULL
);
CREATE INDEX ON core.sales (sale_date, branch);

CREATE VIEW mart.sales_by_branch_month AS
SELECT date_trunc('month', sale_date)::date AS month,
       branch,
       sum(amount)                          AS total_amount,
       count(*)                             AS rows_count
FROM core.sales
GROUP BY 1, 2;

RESET ROLE;
EOSQL
