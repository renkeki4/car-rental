from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from config import Config
from extensions import db, login_manager

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

@app.route('/')
def index():
    from models import Car
    cars = Car.query.all()
    return render_template('index.html', cars=cars)

@app.route('/register', methods=['GET', 'POST'])
def register():
    from models import User
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        password2 = request.form['password2']
        if password != password2:
            flash('Пароли не совпадают')
            return redirect(url_for('register'))
        if User.query.filter_by(username=username).first():
            flash('Имя пользователя занято')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('Email уже используется')
            return redirect(url_for('register'))
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Регистрация успешна! Теперь войдите.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    from models import User
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter((User.username == username) | (User.email == username)).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Добро пожаловать!')
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль')
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    flash('Вы вышли из системы')
    return redirect(url_for('index'))

@app.route('/add_car', methods=['GET', 'POST'])
@login_required
def add_car():
    from models import Car
    if current_user.role != 'admin':
        flash('Доступ запрещён')
        return redirect(url_for('index'))
    if request.method == 'POST':
        brand = request.form['brand']
        model = request.form['model']
        year = int(request.form['year'])
        body_type = request.form['body_type']
        color = request.form['color']
        price_per_day = float(request.form['price_per_day'])
        description = request.form['description']
        is_available = 'is_available' in request.form
        image_url = None
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                import time
                filename = f"{int(time.time())}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                image_url = f"/static/uploads/{filename}"
        car = Car(
            brand=brand, model=model, year=year,
            body_type=body_type, color=color,
            price_per_day=price_per_day,
            description=description,
            is_available=is_available,
            image_url=image_url
        )
        db.session.add(car)
        db.session.commit()
        flash('Автомобиль добавлен!')
        return redirect(url_for('index'))
    return render_template('add_car.html')

@app.route('/edit_car/<int:car_id>', methods=['GET', 'POST'])
@login_required
def edit_car(car_id):
    from models import Car
    car = Car.query.get_or_404(car_id)
    if current_user.role != 'admin':
        flash('Доступ запрещён')
        return redirect(url_for('index'))
    if request.method == 'POST':
        car.brand = request.form['brand']
        car.model = request.form['model']
        car.year = int(request.form['year'])
        car.body_type = request.form['body_type']
        car.color = request.form['color']
        car.price_per_day = float(request.form['price_per_day'])
        car.description = request.form['description']
        car.is_available = 'is_available' in request.form
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                if car.image_url:
                    old_path = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(car.image_url))
                    if os.path.exists(old_path):
                        os.remove(old_path)
                filename = secure_filename(file.filename)
                import time
                filename = f"{int(time.time())}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                car.image_url = f"/static/uploads/{filename}"
        db.session.commit()
        flash('Данные автомобиля обновлены!')
        return redirect(url_for('index'))
    return render_template('edit_car.html', car=car)

@app.route('/delete_car/<int:car_id>')
@login_required
def delete_car(car_id):
    from models import Car, Rental
    car = Car.query.get_or_404(car_id)
    if current_user.role != 'admin':
        flash('Доступ запрещён')
        return redirect(url_for('index'))
    active_rentals = Rental.query.filter_by(car_id=car_id, status='booked').first()
    if active_rentals:
        flash('Нельзя удалить автомобиль, на который есть активные бронирования')
        return redirect(url_for('index'))
    if car.image_url:
        old_path = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(car.image_url))
        if os.path.exists(old_path):
            os.remove(old_path)
    db.session.delete(car)
    db.session.commit()
    flash('Автомобиль удалён')
    return redirect(url_for('index'))

@app.route('/book/<int:car_id>', methods=['GET', 'POST'])
@login_required
def book_car(car_id):
    from models import Car, Rental
    car = Car.query.get_or_404(car_id)
    if request.method == 'POST':
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d')
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if start_date < today:
            flash('Дата начала не может быть раньше сегодняшнего дня')
            return redirect(url_for('book_car', car_id=car_id))
        if end_date <= start_date:
            flash('Дата окончания должна быть позже даты начала')
            return redirect(url_for('book_car', car_id=car_id))
        existing = Rental.query.filter(
            Rental.car_id == car_id,
            Rental.status != 'cancelled',
            Rental.start_date < end_date,
            Rental.end_date > start_date
        ).first()
        if existing:
            flash('Автомобиль уже забронирован на эти даты')
            return redirect(url_for('book_car', car_id=car_id))
        days = (end_date - start_date).days
        total_cost = days * car.price_per_day
        rental = Rental(
            user_id=current_user.id,
            car_id=car_id,
            start_date=start_date,
            end_date=end_date,
            total_cost=total_cost,
            status='booked'
        )
        db.session.add(rental)
        db.session.commit()
        flash('Автомобиль успешно забронирован!')
        return redirect(url_for('my_rentals'))
    return render_template('book.html', car=car)

@app.route('/my_rentals')
@login_required
def my_rentals():
    from models import Rental
    rentals = Rental.query.filter_by(user_id=current_user.id).order_by(Rental.start_date.desc()).all()
    return render_template('my_rentals.html', rentals=rentals)

@app.route('/cancel_rental/<int:rental_id>')
@login_required
def cancel_rental(rental_id):
    from models import Rental
    rental = Rental.query.get_or_404(rental_id)
    if rental.user_id != current_user.id:
        flash('Это не ваша аренда')
        return redirect(url_for('my_rentals'))
    if rental.status == 'cancelled':
        flash('Аренда уже отменена')
        return redirect(url_for('my_rentals'))
    rental.status = 'cancelled'
    db.session.commit()
    flash('Аренда отменена')
    return redirect(url_for('my_rentals'))

@app.route('/admin/rentals')
@login_required
def admin_rentals():
    if current_user.role != 'admin':
        flash('Доступ запрещён')
        return redirect(url_for('index'))
    from models import Rental
    rentals = Rental.query.order_by(Rental.created_at.desc()).all()
    return render_template('admin_rentals.html', rentals=rentals)

@app.route('/admin/update_rental/<int:rental_id>', methods=['POST'])
@login_required
def admin_update_rental(rental_id):
    from models import Rental
    if current_user.role != 'admin':
        flash('Доступ запрещён')
        return redirect(url_for('index'))
    rental = Rental.query.get_or_404(rental_id)
    new_status = request.form.get('status')
    if new_status in ['booked', 'active', 'completed', 'cancelled']:
        rental.status = new_status
        db.session.commit()
        flash(f'Статус аренды №{rental.id} обновлён на "{new_status}"')
    else:
        flash('Некорректный статус')
    return redirect(url_for('admin_rentals'))

@app.route('/admin/edit_rental/<int:rental_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_rental(rental_id):
    from models import Rental, Car
    if current_user.role != 'admin':
        flash('Доступ запрещён')
        return redirect(url_for('index'))
    rental = Rental.query.get_or_404(rental_id)
    if request.method == 'POST':
        try:
            new_start = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
            new_end = datetime.strptime(request.form['end_date'], '%Y-%m-%d')
            if new_end <= new_start:
                flash('Дата окончания должна быть позже даты начала')
                return redirect(url_for('admin_edit_rental', rental_id=rental.id))
            conflict = Rental.query.filter(
                Rental.car_id == rental.car_id,
                Rental.id != rental.id,
                Rental.status != 'cancelled',
                Rental.start_date < new_end,
                Rental.end_date > new_start
            ).first()
            if conflict:
                flash('На эти даты автомобиль уже забронирован')
                return redirect(url_for('admin_edit_rental', rental_id=rental.id))
            days = (new_end - new_start).days
            total_cost = days * rental.car.price_per_day
            rental.start_date = new_start
            rental.end_date = new_end
            rental.total_cost = total_cost
            db.session.commit()
            flash('Даты аренды успешно обновлены!')
            return redirect(url_for('admin_rentals'))
        except ValueError:
            flash('Неверный формат даты')
            return redirect(url_for('admin_edit_rental', rental_id=rental.id))
    return render_template('admin_edit_rental.html', rental=rental)

@app.route('/admin/delete_rental/<int:rental_id>')
@login_required
def admin_delete_rental(rental_id):
    from models import Rental
    if current_user.role != 'admin':
        flash('Доступ запрещён')
        return redirect(url_for('index'))
    rental = Rental.query.get_or_404(rental_id)
    db.session.delete(rental)
    db.session.commit()
    flash('Аренда удалена')
    return redirect(url_for('admin_rentals'))

if __name__ == '__main__':
    from models import User, Car, Rental
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', debug=True, port=5000)
