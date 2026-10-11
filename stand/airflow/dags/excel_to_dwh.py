"""ETL: Excel из папки inbox -> raw -> core в DWH PostgreSQL.

Папка /opt/airflow/inbox в контейнере соответствует ./data/inbox в репозитории.
В боевом контуре вместо неё монтируется сетевая папка (CIFS/SMB), доступная только на чтение,
а обработанные файлы переносятся в отдельное место, куда у сервисной учётки есть запись.

Повторная загрузка файла с тем же именем заменяет его прежние данные (идемпотентность).
"""
from __future__ import annotations

import shutil
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from airflow.decorators import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook
from etl.excel_validation import ValidationError, read_and_validate
from psycopg2.extras import execute_values

INBOX = Path("/opt/airflow/inbox")
ARCHIVE = INBOX / "archive"
REJECTED = INBOX / "rejected"
CONN_ID = "dwh_postgres"


def _log(hook: PostgresHook, source_file: str, status: str, rows: int, message: str | None) -> None:
    hook.run(
        "INSERT INTO raw.load_log (source_file, status, rows_loaded, message) VALUES (%s, %s, %s, %s)",
        parameters=(source_file, status, rows, message),
    )


def _move(path: Path, target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.move(str(path), str(target_dir / f"{stamp}_{path.name}"))


@dag(
    dag_id="excel_to_dwh",
    schedule="*/15 * * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,  # два запуска одновременно не должны делить одни файлы
    default_args={"retries": 1, "retry_delay": timedelta(minutes=2)},
    tags=["etl", "excel"],
)
def excel_to_dwh():
    @task
    def load_files_to_raw() -> int:
        """Грузит каждый новый .xlsx в raw.sales_excel. Возвращает число загруженных файлов."""
        # Временные файлы Excel (~$...) пропускаем
        files = sorted(p for p in INBOX.glob("*.xlsx") if not p.name.startswith("~$"))
        hook = PostgresHook(postgres_conn_id=CONN_ID)
        loaded = 0

        for path in files:
            try:
                df = read_and_validate(path)
            except ValidationError as exc:
                _log(hook, path.name, "rejected", 0, str(exc))
                _move(path, REJECTED)
                continue

            rows = [
                (
                    path.name,
                    int(r.row_num),
                    r.sale_date,
                    r.branch,
                    None if pd.isna(r.product) else str(r.product),  # пустой товар -> NULL
                    float(r.amount),
                )
                for r in df.itertuples(index=False)
            ]
            conn = hook.get_conn()
            try:
                with conn:  # одна транзакция: удалить старое, вставить новое, записать в журнал
                    with conn.cursor() as cur:
                        cur.execute("DELETE FROM raw.sales_excel WHERE source_file = %s", (path.name,))
                        execute_values(
                            cur,
                            "INSERT INTO raw.sales_excel "
                            "(source_file, row_num, sale_date, branch, product, amount) VALUES %s",
                            rows,
                        )
                        cur.execute(
                            "INSERT INTO raw.load_log (source_file, status, rows_loaded) VALUES (%s, 'loaded', %s)",
                            (path.name, len(rows)),
                        )
            finally:
                conn.close()

            _move(path, ARCHIVE)  # переносим только после успешного коммита
            loaded += 1

        return loaded

    @task
    def rebuild_core(loaded_files: int) -> None:
        """Пересобирает core.sales из raw. Для учебных объёмов это проще и надёжнее инкремента."""
        if loaded_files == 0:
            return
        hook = PostgresHook(postgres_conn_id=CONN_ID)
        hook.run(
            [
                "TRUNCATE core.sales",
                "INSERT INTO core.sales (sale_date, branch, product, amount, source_file) "
                "SELECT sale_date, branch, product, amount, source_file FROM raw.sales_excel",
            ],
            autocommit=False,  # обе команды в одной транзакции
        )

    rebuild_core(load_files_to_raw())


excel_to_dwh()
