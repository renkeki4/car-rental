from extensions import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='client')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    rentals = db.relationship('Rental', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    body_type = db.Column(db.String(30))
    color = db.Column(db.String(30))
    price_per_day = db.Column(db.Float, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    image_url = db.Column(db.String(200))
    description = db.Column(db.Text)
    rentals = db.relationship('Rental', backref='car', lazy=True)

    def is_booked_now(self):
        """Проверяет, есть ли активное бронирование на текущий момент."""
        now = datetime.now()
        rental = Rental.query.filter(
            Rental.car_id == self.id,
            Rental.status.in_(['booked', 'active']),
            Rental.start_date <= now,
            Rental.end_date >= now
        ).first()
        return rental is not None

class Rental(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    car_id = db.Column(db.Integer, db.ForeignKey('car.id'), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    total_cost = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='booked')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)