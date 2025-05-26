from os import getenv
from django.core.management.utils import get_random_secret_key


# URL приложения
APPLICATION_URL = getenv('APPLICATION_URL') or ''

# Режим отладки
DEBUG = bool(getenv("DEBUG")) or False

# Секретный ключ
SECRET_KEY = getenv("SECRET_KEY") or get_random_secret_key()

# База данных
DATABASE_HOST = getenv("DATABASE_HOST") or ''
DATABASE_PORT = getenv("DATABASE_PORT") or ''
DATABASE_USER = getenv("DATABASE_USER") or ''
DATABASE_PASSWORD = getenv("DATABASE_PASSWORD") or ''
DATABASE_NAME = getenv("DATABASE_NAME") or ''
