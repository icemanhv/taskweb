from datetime import datetime

from flask import Flask, render_template, redirect, url_for, request, flash, session, abort
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from sqlalchemy.orm import joinedload

from database import db, get_model_fields, get_tables_name
from models import User, getModel, Product, Review

app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = '12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.app_context().push()
db.init_app(app)

login = LoginManager(app)

@login.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route('/')
def index():
    products = Product.query.filter(Product.id.between(0, 10)).all()
    return render_template('index.html', products=products)

@app.route('/product/<product_id>', methods=['GET', 'POST'])
def product(product_id):
    if request.method == 'POST':
        review_text = request.form['review_text']
        review_rate = request.form['review_rate']
        review = Review()
        review.rate = review_rate
        review.created_at = datetime.now()
        review.updated_at = datetime.now()
        review.text = review_text
        review.id_user = current_user.id
        review.id_product = product_id
        prod = db.session.get(Product, product_id)                                                                      # получение продукта
        num_rates = len(prod.reviews)                                                                                   # общее количество отзывов о продукте
        total_rate = num_rates * prod.avg_rate                                                                      # сумма всех оценок отзывов
        total_rate = total_rate + float(review_rate)
        prod.avg_rate = total_rate / (num_rates + 1)                                                                # дополняем среднюю оценку одним отзывом
        db.session.add(review)
        db.session.commit()
    prod = db.session.get(Product, product_id)
    len(prod.reviews)
    reviews = db.session.query(Review).options(joinedload(Review.user)).filter(Review.id_product == product_id).all()
    return render_template('product.html', product=prod, reviews=reviews)


# Корзина
@app.route('/cart')
def cart():
    if 'cart' not in session or not session['cart']:
        return render_template('cart.html', cart_items=None, total=0)
    cart_items = []
    total = 0

    for product_id, item in session['cart'].items():
        product = Product.query.get(product_id)
        if product:
            item_total = product.price * item['quantity']
            cart_items.append({
                'product': product,
                'quantity': item['quantity'],
                'total': item_total
            })
            total += item_total
    return render_template('cart.html', cart_items=cart_items, total=total)


# Добавление в корзину
@app.route('/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    quantity = int(request.form.get('quantity', 1))
    if quantity < 1 or quantity > product.stock:
        flash('Недопустимое количество', 'danger')
        return redirect(url_for('product', product_id=product_id))
    cart = session.get('cart', {})
    if str(product_id) in cart:
        cart[str(product_id)]['quantity'] += quantity
    else:
        cart[str(product_id)] = {
            'quantity': quantity,
            'name': product.name,
            'price': float(product.price),
        }
    session['cart'] = cart
    flash(f'"{product.name}" добавлен в корзину', 'success')
    return redirect(url_for('product', product_id=product_id))


# Обновление корзины
@app.route('/update_cart/<int:product_id>', methods=['POST'])
def update_cart(product_id):
    if 'cart' not in session or str(product_id) not in session['cart']:
        abort(404)
    quantity = int(request.form.get('quantity', 1))
    product = Product.query.get_or_404(product_id)
    if quantity < 1:
        return remove_from_cart(product_id)
    if quantity > product.stock:
        flash('Недостаточно товара на складе', 'danger')
        return redirect(url_for('cart'))
    session['cart'][str(product_id)]['quantity'] = quantity
    session.modified = True
    flash('Корзина обновлена', 'success')
    return redirect(url_for('cart'))


# Удаление из корзины
@app.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    if 'cart' not in session or str(product_id) not in session['cart']:
        abort(404)
    product_name = session['cart'][str(product_id)]['name']
    del session['cart'][str(product_id)]
    session.modified = True
    flash(f'"{product_name}" удален из корзины', 'info')
    return redirect(url_for('cart'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/auth/register/', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index', username=current_user.name))
    if request.method == 'POST':
        form_name = request.form['name']
        form_email = request.form['email']
        form_password = request.form['password']
        if User.query.filter_by(email=form_email).first() :
            flash('Такой пользователь уже существует')
        user = User()
        user.name = form_name
        user.email = form_email
        user.set_password(form_password)

        db.session.add(user)
        db.session.commit()
        return redirect(url_for('/auth/login'))
    return render_template('/auth/register.html')

@app.route('/auth/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        print("already auth")
        return redirect(url_for('index'))
    if request.method == 'POST':
        form_email = request.form['email']
        form_password = request.form['password']
        user = User.query.filter_by(email=form_email).first()
        if user and user.check_password(form_password):
            print("login accept")
            login_user(user)
            return redirect(url_for('index'))
        flash("Неверно введенные данные", 'danger')
    return render_template('/auth/login.html')

@app.route('/auth/logout')
@login_required
def logout():
    logout_user()
    return redirect('/auth/login')

@app.route('/admin')
@login_required
def admin():
    tables = get_tables_name()
    return render_template('/admin/main.html', tables=tables)

@app.route('/admin/tables/<name>', methods=['GET', 'POST'])
@login_required
def admin_tables(name):
    if request.method == 'POST':
        model = getModel(name)()
        model.set_values(request.form)
        db.session.add(model)
        db.session.commit()
    tables = get_tables_name()
    fields = get_model_fields(getModel(name))
    fkdict = dict()
    for field in fields:
        if field['foreign_key']:
            col = list(field['foreign_key'])[0].column
            res = db.session.query(col.table).all()
            fkdict[field['name']] = res
    fields_data = getModel(name).query.all()
    return render_template('/admin/basicTable.html',tables=tables, tablename=name, fields=fields, data=fields_data, fkdict=fkdict)

if __name__ == '__main__':
    app.run(debug=True)