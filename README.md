1...

1.x Прописать

2. Установка и настройка PostgreSQL:

1.1. Установка.
sudo apt install postgres
sudo apt install python-psycopg2
sudo apt install libpq-dev

1.2. Установка пароля доступа.

su
su - postgres
psql
\password

1.3. Создание базы данных.

su
su - postgres
psql
CREATE DATABASE имя_базы

имя_базы - база, которую Вы пропишете в конфиге приложения Flask.


1.4. Прописать адрес подключения к PostgreSQL в приложении Flask.
config.py:
SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:password@localhost/имя_базы'

password -  пароль, заданный в пункте 1.2



