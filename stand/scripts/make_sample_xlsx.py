"""Создаёт тестовые Excel-файлы в data/inbox: один корректный и один с ошибками.

Запуск (из корня репозитория):
    pip install pandas openpyxl
    python scripts/make_sample_xlsx.py
"""
from pathlib import Path

import pandas as pd

INBOX = Path(__file__).resolve().parent.parent / "data" / "inbox"
INBOX.mkdir(parents=True, exist_ok=True)

good = pd.DataFrame(
    {
        "Дата": ["01.10.2026", "02.10.2026", "03.10.2026", "03.10.2026"],
        "Филиал": ["Бишкек", "Бишкек", "Ош", "Ош"],
        "Товар": ["Цемент", "Арматура", "Цемент", "Кирпич"],
        "Сумма": [15000.5, "27 300,00", 8200, 12100.75],
    }
)
good.to_excel(INBOX / "sales_good.xlsx", index=False)

bad = pd.DataFrame(
    {
        "Дата": ["04.10.2026", "не дата", "06.10.2026"],
        "Филиал": ["Бишкек", "Ош", None],
        "Товар": ["Цемент", "Кирпич", "Арматура"],
        "Сумма": [1000, "abc", 500],
    }
)
bad.to_excel(INBOX / "sales_bad.xlsx", index=False)

print(f"Созданы файлы в {INBOX}: sales_good.xlsx, sales_bad.xlsx")
