import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    
    # Путь к базе данных (создаём папку instance)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
    if not os.path.exists(INSTANCE_DIR):
        os.makedirs(INSTANCE_DIR)
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(INSTANCE_DIR, "rental.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Настройки для загрузки фото
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    # Создаём папку, если её нет
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    LOGIN_VIEW = 'login'
    LOGIN_MESSAGE = 'Пожалуйста, войдите для доступа к этой странице.'