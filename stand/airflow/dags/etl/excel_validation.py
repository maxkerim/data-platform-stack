"""Чтение и валидация Excel-файла с продажами.

Вынесено из DAG-а, чтобы логику можно было тестировать без Airflow.
Правило: если в файле есть хотя бы одна плохая строка, он отклоняется целиком
и в сообщении указываются номера строк Excel. Так в DWH не попадают частичные данные.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

# Допустимые названия колонок (регистр и пробелы по краям не важны) -> имя в БД
HEADER_ALIASES = {
    "date": "sale_date",
    "дата": "sale_date",
    "branch": "branch",
    "филиал": "branch",
    "product": "product",
    "товар": "product",
    "продукт": "product",
    "amount": "amount",
    "сумма": "amount",
}
REQUIRED_COLUMNS = ["sale_date", "branch", "amount"]
MAX_ERRORS_IN_MESSAGE = 10


class ValidationError(Exception):
    """Файл не прошёл проверку. Текст понятен человеку и уходит в журнал."""


def _normalize_headers(df: pd.DataFrame) -> pd.DataFrame:
    renamed = {}
    for col in df.columns:
        key = str(col).strip().lower()
        if key in HEADER_ALIASES:
            renamed[col] = HEADER_ALIASES[key]
    df = df.rename(columns=renamed)
    # Лишние колонки игнорируем, но не теряем молча важные
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValidationError(
            f"Не найдены обязательные колонки: {', '.join(missing)}. "
            f"Ожидаются заголовки в первой строке: Дата, Филиал, Сумма (опционально Товар)."
        )
    if "product" not in df.columns:
        df["product"] = None
    return df[["sale_date", "branch", "product", "amount"]]


def read_and_validate(path: Path) -> pd.DataFrame:
    """Возвращает DataFrame с колонками sale_date, branch, product, amount, row_num.

    Бросает ValidationError, если файл нельзя загрузить.
    """
    try:
        raw = pd.read_excel(path, engine="openpyxl")
    except Exception as exc:  # битый файл, не xlsx, защищён паролем и т.п.
        raise ValidationError(f"Не удалось открыть файл как Excel: {exc}") from exc

    raw = raw.dropna(how="all")  # пустые строки в конце листа
    if raw.empty:
        raise ValidationError("В файле нет данных под заголовком.")

    # Номер строки в Excel: индекс pandas + 2 (заголовок = строка 1, индекс с 0)
    row_numbers = raw.index + 2
    df = _normalize_headers(raw)
    df["row_num"] = row_numbers

    df["sale_date"] = pd.to_datetime(df["sale_date"], errors="coerce", dayfirst=True).dt.date

    amount_text = (
        df["amount"].astype(str).str.replace(r"\s", "", regex=True).str.replace(",", ".", regex=False)
    )
    df["amount"] = pd.to_numeric(amount_text, errors="coerce")

    df["branch"] = df["branch"].astype(str).str.strip()
    df.loc[df["branch"].isin(["", "nan", "None"]), "branch"] = None
    df["product"] = df["product"].where(df["product"].notna(), None)

    problems = []
    for _, row in df.iterrows():
        bad = []
        if pd.isna(row["sale_date"]):
            bad.append("дата")
        if row["branch"] is None or pd.isna(row["branch"]):
            bad.append("филиал")
        if pd.isna(row["amount"]):
            bad.append("сумма")
        if bad:
            problems.append(f"строка {row['row_num']}: проверьте {', '.join(bad)}")

    if problems:
        shown = "; ".join(problems[:MAX_ERRORS_IN_MESSAGE])
        extra = len(problems) - MAX_ERRORS_IN_MESSAGE
        suffix = f" (и ещё {extra})" if extra > 0 else ""
        raise ValidationError(f"Ошибки в {len(problems)} строках: {shown}{suffix}")

    df["amount"] = df["amount"].round(2)
    return df.reset_index(drop=True)
