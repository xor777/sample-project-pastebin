#!/usr/bin/env python3

import os
import random
import string
import logging
import pymysql
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, redirect, url_for, abort

load_dotenv(override=True)

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

logging.basicConfig(level=logging.INFO)

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASS', ''),
    'db': os.getenv('DB_NAME', 'mini_pastebin'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    try:
        connection = pymysql.connect(**DB_CONFIG)
        return connection
    except pymysql.Error as e:
        app.logger.error(f"Не удалось подключиться к базе данных: {e}")
        return None

def generate_slug(length=6):
    characters = string.ascii_lowercase + string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def create_snippet(content):
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        slug = generate_slug()
        attempts = 0
        max_attempts = 10
        
        with connection.cursor() as cursor:
            while attempts < max_attempts:
                cursor.execute("SELECT 1 FROM snippets WHERE slug = %s", (slug,))
                if not cursor.fetchone():
                    break
                slug = generate_slug()
                attempts += 1
            
            if attempts >= max_attempts:
                app.logger.error("Не удалось сгенерировать уникальный идентификатор")
                return None
            
            cursor.execute(
                "INSERT INTO snippets (slug, content) VALUES (%s, %s)",
                (slug, content)
            )
            connection.commit()
            return slug
    except pymysql.Error as e:
        app.logger.error(f"Ошибка базы данных при создании сниппета: {e}")
        return None
    finally:
        connection.close()

def get_snippet(slug):
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM snippets WHERE slug = %s",
                (slug,)
            )
            return cursor.fetchone()
    except pymysql.Error as e:
        app.logger.error(f"Ошибка базы данных при получении сниппета: {e}")
        return None
    finally:
        connection.close()

def list_snippets(limit=10):
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, slug, LEFT(content, 100) as preview, created_at "
                "FROM snippets ORDER BY created_at DESC LIMIT %s",
                (limit,)
            )
            return cursor.fetchall()
    except pymysql.Error as e:
        app.logger.error(f"Ошибка базы данных при получении списка сниппетов: {e}")
        return None
    finally:
        connection.close()

def delete_snippet(slug):
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM snippets WHERE slug = %s", (slug,))
            connection.commit()
            return cursor.rowcount > 0
    except pymysql.Error as e:
        app.logger.error(f"Ошибка базы данных при удалении сниппета: {e}")
        return False
    finally:
        connection.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create', methods=['POST'])
def create():
    if request.is_json:
        data = request.get_json()
        content = data.get('content', '')
    else:
        content = request.form.get('content', '')
    
    if not content:
        return jsonify({"error": "Содержимое не может быть пустым"}), 400
    
    slug = create_snippet(content)
    if not slug:
        return jsonify({"error": "Не удалось создать сниппет. Ошибка базы данных."}), 500
    
    if request.is_json:
        return jsonify({
            "slug": slug,
            "url": url_for('view_snippet', slug=slug, _external=True)
        }), 201
    else:
        return redirect(url_for('view_snippet', slug=slug))

@app.route('/p/<slug>')
def view_snippet(slug):
    snippet = get_snippet(slug)
    
    if not snippet:
        abort(404)
    
    if request.headers.get('Accept') == 'application/json':
        return jsonify({
            "slug": snippet['slug'],
            "content": snippet['content'],
            "created_at": snippet['created_at'].isoformat()
        })
    else:
        return render_template('snippet.html', snippet=snippet)

@app.route('/list')
def list_all():
    snippets = list_snippets(limit=20)
    
    if snippets is None:
        return jsonify({"error": "Не удалось получить список сниппетов. Ошибка базы данных."}), 500
    
    if request.headers.get('Accept') == 'application/json':
        return jsonify([{
            "slug": s['slug'],
            "preview": s['preview'],
            "created_at": s['created_at'].isoformat()
        } for s in snippets])
    else:
        return render_template('list.html', snippets=snippets)

@app.route('/p/<slug>', methods=['DELETE'])
def delete(slug):
    success = delete_snippet(slug)
    
    if not success:
        abort(404)
    
    return '', 204

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error="Сниппет не найден"), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('error.html', error="Ошибка сервера. Пожалуйста, попробуйте позже."), 500

def check_db():
    connection = get_db_connection()
    if not connection:
        app.logger.error("Не удалось подключиться к базе данных при запуске")
    else:
        connection.close()
        app.logger.info("Подключение к базе данных успешно")

if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    
    flask_port = os.getenv('FLASK_PORT')
    port = int(flask_port) if flask_port else 5001
    
    debug = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    
    check_db()
    
    app.run(host=host, port=port, debug=debug) 