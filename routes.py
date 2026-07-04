from app import app
from flask import render_template

# Мы перенесём маршруты сюда позже, а пока оставим заглушку
@app.route('/')
def index():
    return 'Приложение работает! (routes)'