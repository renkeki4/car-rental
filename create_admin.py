from app import app, db
from models import User

with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@example.com', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('Администратор создан: логин admin, пароль admin123')
    else:
        print('Администратор уже существует')