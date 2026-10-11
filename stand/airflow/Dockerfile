ARG BASE_REGISTRY=""
FROM ${BASE_REGISTRY}apache/airflow:2.10.5

# pandas и провайдер PostgreSQL уже есть в образе, добавляем только чтение .xlsx.
# В закрытом контуре эта установка идёт через внутреннее зеркало PyPI.
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt
