#!/usr/bin/env python3

import os
import sys
import logging
import pymysql
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASS', ''),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

DB_NAME = os.getenv('DB_NAME', 'mini_pastebin')

def get_connection():
    try:
        connection = pymysql.connect(**DB_CONFIG)
        return connection
    except pymysql.Error as e:
        logger.error(f"Не удалось подключиться к базе данных: {e}")
        sys.exit(1)

def init_database():
    try:
        connection = get_connection()
        
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            logger.info(f"База данных '{DB_NAME}' создана или уже существует")
            
            cursor.execute(f"USE {DB_NAME}")

            cursor.execute("DROP TABLE IF EXISTS snippets")
            
            create_table_sql = """
            CREATE TABLE snippets (
                id INT AUTO_INCREMENT PRIMARY KEY,
                slug VARCHAR(10) NOT NULL UNIQUE,
                content TEXT NOT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,
                INDEX (slug)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            cursor.execute(create_table_sql)
            
            connection.commit()
            logger.info("Таблица 'snippets' успешно создана")
            
    except pymysql.Error as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
        sys.exit(1)
    finally:
        connection.close()

def check_database():
    try:
        connection = get_connection()
        
        with connection.cursor() as cursor:
            cursor.execute("SHOW DATABASES LIKE %s", (DB_NAME,))
            if not cursor.fetchone():
                logger.warning(f"База данных '{DB_NAME}' не существует")
                return False
            
            cursor.execute(f"USE {DB_NAME}")
            
            cursor.execute("SHOW TABLES LIKE 'snippets'")
            if not cursor.fetchone():
                logger.warning("Таблица 'snippets' не существует")
                return False
            
            cursor.execute("DESCRIBE snippets")
            columns = {row['Field']: row for row in cursor.fetchall()}
            
            required_columns = ['id', 'slug', 'content', 'created_at']
            for col in required_columns:
                if col not in columns:
                    logger.warning(f"В таблице 'snippets' отсутствует обязательный столбец: {col}")
                    return False
            
            logger.info("База данных и структура таблицы успешно проверены")
            return True
            
    except pymysql.Error as e:
        logger.error(f"Ошибка при проверке базы данных: {e}")
        return False
    finally:
        connection.close()

def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'init':
        logger.info("Инициализация базы данных...")
        init_database()
    else:
        if check_database():
            logger.info("База данных готова к использованию")
        else:
            logger.warning("База данных не настроена должным образом. Запустите 'python db_manage.py init' для инициализации.")
            sys.exit(1)

if __name__ == "__main__":
    main() 