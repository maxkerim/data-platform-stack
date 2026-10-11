ARG BASE_REGISTRY=""
FROM ${BASE_REGISTRY}apache/superset:5.0.0

# В базовом образе нет драйвера PostgreSQL, добавляем его в виртуальное окружение Superset.
# В закрытом контуре установка идёт через внутреннее зеркало PyPI.
USER root
RUN . /app/.venv/bin/activate && uv pip install --no-cache-dir psycopg2-binary
USER superset
