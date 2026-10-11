"""Конфигурация Superset для тренировочного стенда. Секреты берутся из переменных окружения."""
import os

SECRET_KEY = os.environ["SUPERSET_SECRET_KEY"]

# Служебная БД Superset (не DWH!)
SQLALCHEMY_DATABASE_URI = (
    f"postgresql+psycopg2://superset:{os.environ['SUPERSET_DB_PASSWORD']}@postgres:5432/superset"
)

# Кеш результатов запросов и метаданных в Redis
CACHE_CONFIG = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 300,
    "CACHE_KEY_PREFIX": "superset_",
    "CACHE_REDIS_URL": "redis://redis:6379/0",
}
DATA_CACHE_CONFIG = {**CACHE_CONFIG, "CACHE_KEY_PREFIX": "superset_data_"}

# Для учебного стенда по HTTP. В проде за nginx с TLS эти флаги включаются.
TALISMAN_ENABLED = False
SESSION_COOKIE_SECURE = False
WTF_CSRF_ENABLED = True
